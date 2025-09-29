"""
Harris County Property Records Scraper - Class-based implementation.
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from config import DEFAULT_HEADERS, HARRIS_COUNTY_BASE_URL, REQUEST_TIMEOUT
import os
from utils.logger_config import get_scraper_logger

# Configure logging
logger = get_scraper_logger()


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
        
        # Create a session for connection reuse
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.timeout = timeout
        
        # Initialize login and security params
        self.login()
        self.security_params = self._get_security_params()
        # Only log initialization once per session
        if not hasattr(self, '_init_logged'):
            logger.info("Harris County scraper initialized successfully with session-based HTTP client")
            self._init_logged = True
    
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
        response = self.session.post(self.search_url)
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
        response = self.session.get(
            "https://www.cclerk.hctx.net/Applications/WebSearch/Registration/Login.aspx"
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
        response = self.session.post(
            "https://www.cclerk.hctx.net/Applications/WebSearch/Registration/Login.aspx",
            data=data
        )
        if response.url.endswith("/Applications/WebSearch/Home.aspx"):
            # Only log authentication success once per session
            if not hasattr(self, '_login_logged'):
                logger.info("Successfully authenticated with Harris County Clerk's website")
                self._login_logged = True
        else:
            logger.error(f"Authentication failed - unexpected redirect to: {response.url}")
            raise Exception("Login failed - invalid credentials or network issue")
    
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
            logger.info(f"Starting search for instrument type '{instrument_type}' from {start_date} to {end_date}")
            
            data = self._prepare_search_data(instrument_type, start_date, end_date)
            logger.debug(f"Prepared search data with {len(data)} form fields")
            
            response = self.session.post(
                self.search_url,
                data=data
            )
            
            response.raise_for_status()
            logger.info(f"Successfully retrieved search results for '{instrument_type}' - Status: {response.status_code}, Content-Length: {len(response.content)} bytes")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during search for '{instrument_type}': {type(e).__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during search for '{instrument_type}': {type(e).__name__}: {e}")
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
            logger.info(f"Found {len(rows)} result rows in HTML response to parse")
            
            if not rows:
                logger.warning("No result rows found in HTML response - possible empty search results")
                return pd.DataFrame()
            
            successful_parses = 0
            for i, row in enumerate(rows):
                record = self._parse_record_row(row)
                if record:
                    data.append(record)
                    successful_parses += 1
                else:
                    logger.debug(f"Failed to parse row {i+1}/{len(rows)}")
            
            df = pd.DataFrame(data)
            logger.info(f"Successfully parsed {successful_parses}/{len(rows)} records into DataFrame with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing HTML response: {type(e).__name__}: {e}")
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
            logger.info(f"Starting complete scrape operation for instrument type '{instrument_type}' from {start_date} to {end_date}")
            
            # Search for records
            html = self.search_records(instrument_type, start_date, end_date)
            if not html:
                logger.warning(f"No HTML response received for '{instrument_type}' - search may have failed")
                return pd.DataFrame()
            
            # Parse the response
            df = self.parse_html_response(html)
            
            if df.empty:
                logger.warning(f"No records found for instrument type '{instrument_type}' in date range {start_date} to {end_date}")
            else:
                logger.info(f"Scrape operation completed successfully - found {len(df)} records for '{instrument_type}'")
            
            return df
            
        except Exception as e:
            logger.error(f"Scrape operation failed for '{instrument_type}': {type(e).__name__}: {e}")
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
    
    def download_pdf(self, pdf_url: str, output_path: str) -> bool:
        """
        Download a PDF file from the given URL.
        
        Args:
            pdf_url: URL of the PDF to download
            output_path: Local path where to save the PDF
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            logger.info(f"Starting PDF download from: {pdf_url}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"Created output directory: {output_dir}")
            
            # Download the PDF
            response = self.session.get(pdf_url, stream=True)
            response.raise_for_status()
            
            # Get file size from headers
            content_length = response.headers.get('content-length')
            file_size = int(content_length) if content_length else 'unknown'
            logger.info(f"PDF download response - Status: {response.status_code}, Size: {file_size} bytes")
            
            # Save the PDF
            with open(output_path, 'wb') as f:
                downloaded_bytes = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
            
            # Verify download
            actual_size = os.path.getsize(output_path)
            logger.info(f"PDF download completed successfully - saved to: {output_path} ({actual_size:,} bytes)")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during PDF download from {pdf_url}: {type(e).__name__}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {type(e).__name__}: {e}")
            return False
    
    def download_pdfs_from_records(self, records_df: pd.DataFrame, output_dir: str = "downloads") -> Dict[str, bool]:
        """
        Download PDFs for all records that have FilmCode and PDF URLs.
        
        Args:
            records_df: DataFrame containing scraped records
            output_dir: Directory to save downloaded PDFs
            
        Returns:
            Dictionary mapping record IDs to download success status
        """
        try:
            logger.info(f"Starting bulk PDF download for {len(records_df)} records to directory: {output_dir}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            download_results = {}
            successful_downloads = 0
            failed_downloads = 0
            
            for index, record in records_df.iterrows():
                record_id = record.get('FileNo', f'record_{index}')
                
                # Check if record has FilmCode and PDF URL
                if not record.get('FilmCode'):
                    logger.debug(f"Skipping record {record_id} - no FilmCode")
                    download_results[record_id] = False
                    continue
                
                # Construct PDF URL if not already present
                if 'PdfUrl' not in record or not record['PdfUrl']:
                    # Try to construct URL from FilmCode
                    pdf_url = f"https://www.cclerk.hctx.net/Applications/WebSearch/{record['FilmCode']}"
                else:
                    pdf_url = record['PdfUrl']
                
                # Generate output filename
                safe_filename = f"{record_id}_{record.get('FileDate', 'unknown')}.pdf"
                safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('-', '_', '.'))
                output_path = os.path.join(output_dir, safe_filename)
                
                # Download the PDF
                success = self.download_pdf(pdf_url, output_path)
                download_results[record_id] = success
                
                if success:
                    successful_downloads += 1
                    logger.info(f"Successfully downloaded PDF for record {record_id}")
                else:
                    failed_downloads += 1
                    logger.warning(f"Failed to download PDF for record {record_id}")
            
            logger.info(f"Bulk PDF download completed - Success: {successful_downloads}, Failed: {failed_downloads}")
            return download_results
            
        except Exception as e:
            logger.error(f"Bulk PDF download operation failed: {type(e).__name__}: {e}")
            return {}
    
    def close_session(self):
        """Close the requests session."""
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("HTTP session closed successfully")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close_session()


# Global scraper instance for efficiency
_scraper_instance = None

def get_scraper() -> HarrisCountyScraper:
    """Get the global scraper instance (singleton pattern)."""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = HarrisCountyScraper()
    return _scraper_instance

def close_scraper():
    """Close the global scraper instance and its session."""
    global _scraper_instance
    if _scraper_instance is not None:
        _scraper_instance.close_session()
        _scraper_instance = None
        logger.info("Global scraper singleton instance closed and reset")

# Backward compatibility functions using single instance
def get_html_table(instrument_type: str, starting_date: str, ending_date: str) -> str:
    """Backward compatibility function."""
    return get_scraper().search_records(instrument_type, starting_date, ending_date) or ""


def parse_html_to_excel(html: str) -> pd.DataFrame:
    """Backward compatibility function."""
    return get_scraper().parse_html_response(html)


def get_table(instrument_type: str, starting_date: str, ending_date: str) -> pd.DataFrame:
    """Backward compatibility function."""
    return get_scraper().scrape_records(instrument_type, starting_date, ending_date)
