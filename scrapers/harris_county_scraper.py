"""
Harris County Property Records Scraper - Class-based implementation.
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
import logging
from datetime import datetime
from config import DEFAULT_HEADERS, HARRIS_COUNTY_BASE_URL, REQUEST_TIMEOUT
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HarrisCountyScraper:
    """Class-based scraper for Harris County property records."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Initialize the Harris County scraper.
        
        Args:
            headers: Custom headers for requests (optional)
            timeout: Request timeout in seconds
        """
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.timeout = timeout
        self.base_url = HARRIS_COUNTY_BASE_URL
        self.HCTX_USERNAME = os.getenv("HCTX_USERNAME")
        self.HCTX_PASSWORD = os.getenv("HCTX_PASSWORD")
        self.search_url = self._get_search_url()
        self.login()
        self.security_params = self._get_security_params()
        logger.info("Harris County scraper initialized")
    
    def _get_search_url(self) -> str:
        """Get the search URL for Harris County records."""
        return (
            'https://www.cclerk.hctx.net/Applications/WebSearch/RP_R.aspx?ID='
            'PtRyJzbPPV9CWT5QJ8WvKDQ+gLwGxn+WYxPqQJ2yN2nrebuxSt+MLpgoiTw8390k/'
            'FkLbEd+ePVrAgLk58t/pKToXIY6RA7Vlxcm4HNe0h+B44WcgPp55ZpkPH7n9pxaYn8HnDJN/'
            'EGBWxPTWRvRlL5+zpHxYWmIh2BBJUy1a29u0hDndbUlo+Vr2ytEO6ki'
        )
    
    def _get_security_params(self) -> Dict[str, str]:
        """Get the security parameters for Harris County records."""
        response = requests.post(
            self.search_url,
            headers=self.headers,
            timeout=self.timeout
        )
        soup = BeautifulSoup(response.content, "html.parser")
        
        return {
            "__VIEWSTATE":soup.select_one("input#__VIEWSTATE").get("value") or "",
            "__VIEWSTATEGENERATOR":soup.select_one("input#__VIEWSTATEGENERATOR").get("value") or "",
            "__EVENTVALIDATION":soup.select_one("input#__EVENTVALIDATION").get("value") or "",
            "__VIEWSTATEENCRYPTED":soup.select_one("input#__VIEWSTATEENCRYPTED").get("value") or "",
            "__LASTFOCUS":soup.select_one("input#__LASTFOCUS").get("value") or "",
            "__EVENTARGUMENT":soup.select_one("input#__EVENTARGUMENT").get("value") or "",
            "__EVENTTARGET":soup.select_one("input#__EVENTTARGET").get("value") or "",
        }

    def login(self):
        """Login to Harris County Clerk's website."""
        response = requests.get(
            "https://www.cclerk.hctx.net/Applications/WebSearch/Registration/Login.aspx",
            headers=self.headers,
            timeout=self.timeout
        )
        soup = BeautifulSoup(response.content,"html.parser")
        data = {
            "__EVENTTARGET":soup.select_one("input#__EVENTTARGET").get("value") or "",
            "__EVENTARGUMENT":soup.select_one("input#__EVENTARGUMENT").get("value") or "",
            "__VIEWSTATE":soup.select_one("input#__VIEWSTATE").get("value") or "",
            "__VIEWSTATEGENERATOR":soup.select_one("input#__VIEWSTATEGENERATOR").get("value") or "",
            "__VIEWSTATEENCRYPTED":soup.select_one("input#__VIEWSTATEENCRYPTED").get("value") or "",
            "__EVENTVALIDATION":soup.select_one("input#__EVENTVALIDATION").get("value") or "",
        }
        data.update(
            {
            'ctl00$ContentPlaceHolder1$Login1$UserName': self.HCTX_USERNAME,
            'ctl00$ContentPlaceHolder1$Login1$Password': self.HCTX_PASSWORD,
            'ctl00$ContentPlaceHolder1$Login1$LoginButton': 'Log In',
            }
        )
        response = requests.post(
            "https://www.cclerk.hctx.net/Applications/WebSearch/Registration/Login.aspx",
            headers=self.headers,
            data=data,
            timeout=self.timeout
        )
        if response.status_code == 302 and response.headers.get("Location") == "/Applications/WebSearch/Home.aspx":
            logger.info("Login successful")
        else:
            logger.error("Login failed")
            raise Exception("Login failed")
    
    def _prepare_search_data(self, instrument_type: str, start_date: str, end_date: str) -> Dict[str, str]:
        """
        Prepare the search form data.
        
        Args:
            instrument_type: Type of instrument to search for
            start_date: Start date in MM/DD/YYYY format
            end_date: End date in MM/DD/YYYY format
            
        Returns:
            Dictionary containing form data
        """
        search_data = {
            'ctl00$ScriptManager1': 'ctl00$ScriptManager1|ctl00$ContentPlaceHolder1$btnSearch',
            'ctl00$ContentPlaceHolder1$hfSearchType': '0',
            'ctl00$ContentPlaceHolder1$hfViewCopyOrders': 'False',
            'ctl00$ContentPlaceHolder1$hfViewECart': 'False',
            'ctl00$ContentPlaceHolder1$txtFN': '',
            'ctl00$ContentPlaceHolder1$txtFilmCd': '',
            'ctl00$ContentPlaceHolder1$txtDateN': start_date,
            'ctl00$ContentPlaceHolder1$txtDateTo': end_date,
            'ctl00$ContentPlaceHolder1$txtNameOR': '',
            'ctl00$ContentPlaceHolder1$txtNameEE': '',
            'ctl00$ContentPlaceHolder1$txtNameTee': '',
            'ctl00$ContentPlaceHolder1$txtDesc': '',
            'ctl00$ContentPlaceHolder1$txtType': instrument_type,
            'ctl00$ContentPlaceHolder1$txtVolNo': '',
            'ctl00$ContentPlaceHolder1$txtPageNo': '',
            'ctl00$ContentPlaceHolder1$txtSection': '',
            'ctl00$ContentPlaceHolder1$txtLot': '',
            'ctl00$ContentPlaceHolder1$txtBlock': '',
            'ctl00$ContentPlaceHolder1$txtUnit': '',
            'ctl00$ContentPlaceHolder1$txtAbstract': '',
            'ctl00$ContentPlaceHolder1$txtOutLot': '',
            'ctl00$ContentPlaceHolder1$txtTract': '',
            'ctl00$ContentPlaceHolder1$txtReserve': '',
            'ctl00$ContentPlaceHolder1$btnSearch': 'Search',
        }
        search_data.update(self.security_params)
        return search_data
    
    def search_records(self, instrument_type: str, start_date: str, end_date: str) -> Optional[str]:
        """
        Search for records and return HTML response.
        
        Args:
            instrument_type: Type of instrument to search for
            start_date: Start date in MM/DD/YYYY format
            end_date: End date in MM/DD/YYYY format
            
        Returns:
            HTML response text or None if error
        """
        try:
            logger.info(f"Searching for {instrument_type} records from {start_date} to {end_date}")
            
            data = self._prepare_search_data(instrument_type, start_date, end_date)
            
            response = requests.post(
                self.search_url,
                headers=self.headers,
                data=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            logger.info(f"Successfully retrieved {instrument_type} records")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching records: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return None
    
    def parse_html_response(self, html: str) -> pd.DataFrame:
        """
        Parse HTML response and extract record data.
        
        Args:
            html: HTML response text
            
        Returns:
            DataFrame containing parsed records
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            data = []
            
            # Find all result rows
            rows = soup.find_all("tr", class_=["odd", "even"])
            logger.info(f"Found {len(rows)} result rows to parse")
            
            for row in rows:
                record = self._parse_record_row(row)
                if record:
                    data.append(record)
            
            df = pd.DataFrame(data)
            logger.info(f"Successfully parsed {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing HTML response: {e}")
            return pd.DataFrame()
    
    def _parse_record_row(self, row) -> Optional[Dict[str, str]]:
        """
        Parse a single record row.
        
        Args:
            row: BeautifulSoup row element
            
        Returns:
            Dictionary containing record data or None if parsing fails
        """
        try:
            cells = row.find_all("td", recursive=False)
            if not cells or len(cells) < 6:
                return None
            
            record = {}
            
            # Extract basic record information
            record["FileNo"] = self._safe_get_text(cells, 1)
            record["FileDate"] = self._safe_get_text(cells, 2)
            record["DocType"] = self._safe_get_text(cells, 3).split("\n")[0] if self._safe_get_text(cells, 3) else ""
            record["FilmCode"] = self._safe_get_text(cells, 7)
            # Extract Grantors and Grantees
            if len(cells) > 4:
                grantors, grantees = self._extract_parties(cells[4])
                record["Grantors"] = ", ".join(grantors)
                record["Grantees"] = ", ".join(grantees)
            else:
                record["Grantors"] = ""
                record["Grantees"] = ""
            
            # Extract Legal Description
            if len(cells) > 5:
                record["LegalDescription"] = self._extract_legal_description(cells[5])
            else:
                record["LegalDescription"] = ""
            
            if len(cells) >= 2:
                record["Pages"] = self._safe_get_text(cells,-2)
            else:
                record["Pages"] = ""


            record["PdfUrl"] = ""
            if record["FilmCode"]:
                pdfUrl = cells[7].select_one("a").get("href") or ""
                if pdfUrl:
                    record["PdfUrl"] = f"https://www.cclerk.hctx.net/Applications/WebSearch/{pdfUrl}"
               

            return record
            
        except Exception as e:
            logger.error(f"Error parsing record row: {e}")
            return None
    
    def _safe_get_text(self, cells: List, index: int) -> str:
        """Safely get text from cell at index."""
        try:
            return cells[index].get_text(strip=True) or ""
        except Exception:
            return ""
    
    def _extract_parties(self, parties_cell) -> Tuple[List[str], List[str]]:
        """
        Extract Grantors and Grantees from parties cell.
        
        Args:
            parties_cell: BeautifulSoup cell element containing parties
            
        Returns:
            Tuple of (grantors_list, grantees_list)
        """
        grantors = []
        grantees = []
        
        try:
            parties_table = parties_cell.find("table", id="itemPlaceHolderContainer")
            if not parties_table:
                return grantors, grantees
            
            for tr in parties_table.find_all("tr"):
                label = tr.find("b")
                name_span = tr.find("span")
                
                if not label or not name_span:
                    continue
                
                label_text = label.get_text(strip=True)
                name = name_span.get_text(strip=True)
                
                if "Grantor" in label_text:
                    grantors.append(name)
                elif "Grantee" in label_text:
                    grantees.append(name)
                    
        except Exception as e:
            logger.error(f"Error extracting parties: {e}")
        
        return grantors, grantees
    
    def _extract_legal_description(self, legal_cell) -> str:
        """
        Extract legal description from legal description cell.
        
        Args:
            legal_cell: BeautifulSoup cell element containing legal description
            
        Returns:
            Legal description text
        """
        try:
            parts = []
            for span in legal_cell.find_all("span"):
                text = span.get_text(strip=True)
                if text:
                    parts.append(text)
            return " ".join(parts)
        except Exception as e:
            logger.error(f"Error extracting legal description: {e}")
            return ""
    
    def scrape_records(self, instrument_type: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Main method to scrape records for given parameters.
        
        Args:
            instrument_type: Type of instrument to search for
            start_date: Start date in MM/DD/YYYY format
            end_date: End date in MM/DD/YYYY format
            
        Returns:
            DataFrame containing scraped records
        """
        try:
            logger.info(f"Starting scrape for {instrument_type} from {start_date} to {end_date}")
            
            # Search for records
            html = self.search_records(instrument_type, start_date, end_date)
            if not html:
                logger.warning("No HTML response received")
                return pd.DataFrame()
            
            # Parse the response
            df = self.parse_html_response(html)
            
            if df.empty:
                logger.warning("No records found")
            else:
                logger.info(f"Successfully scraped {len(df)} records")
            
            return df
            
        except Exception as e:
            logger.error(f"Error in scrape_records: {e}")
            return pd.DataFrame()
    
    def get_available_instrument_types(self) -> List[str]:
        """
        Get list of available instrument types.
        This would typically be scraped from the website, but for now returns common types.
        
        Returns:
            List of instrument type codes
        """
        return [
            "DEED", "WARRANTY DEED", "QUITCLAIM DEED", "DEED OF TRUST",
            "MORTGAGE", "LIEN", "RELEASE", "ASSIGNMENT", "SATISFACTION"
        ]
    
    def validate_date_format(self, date_str: str) -> bool:
        """
        Validate date format (MM/DD/YYYY).
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except ValueError:
            return False
    
    def get_scraper_info(self) -> Dict[str, str]:
        """
        Get information about the scraper.
        
        Returns:
            Dictionary with scraper information
        """
        return {
            "name": "Harris County Property Records Scraper",
            "version": "2.0.0",
            "base_url": self.base_url,
            "timeout": str(self.timeout),
            "status": "active"
        }


# Backward compatibility functions - these will be replaced by session state usage
def get_html_table(instrument_type: str, starting_date: str, ending_date: str) -> str:
    """Backward compatibility function - use session state in Streamlit apps."""
    scraper = HarrisCountyScraper()
    return scraper.search_records(instrument_type, starting_date, ending_date) or ""


def parse_html_to_excel(html: str) -> pd.DataFrame:
    """Backward compatibility function - use session state in Streamlit apps."""
    scraper = HarrisCountyScraper()
    return scraper.parse_html_response(html)


def get_table(instrument_type: str, starting_date: str, ending_date: str) -> pd.DataFrame:
    """Backward compatibility function - use session state in Streamlit apps."""
    scraper = HarrisCountyScraper()
    return scraper.scrape_records(instrument_type, starting_date, ending_date)
