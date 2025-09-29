"""
HCAD (Harris County Appraisal District) property search scraper.
"""
import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from typing import Dict, List, Optional, Any
from datetime import date

from config import (
    HCAD_BASE_URL,
    HCAD_PROPERTY_SEARCH_URL,
    BROWSER_HEADERS,
    NUM_TABS,
    HEADLESS_MODE,
    BROWSER_TIMEOUT,
    SEARCH_TIMEOUT,
    ADDRESS_PATTERNS,
    NO_RESULTS_INDICATORS
)
from utils.text_processing import clean_legal_description, generate_name_variations, extract_owner_name


class HCADScraper:
    """Scraper for HCAD property search functionality."""
    
    def __init__(self):
        self.base_url = HCAD_BASE_URL
        self.property_search_url = HCAD_PROPERTY_SEARCH_URL
        self.browser_headers = BROWSER_HEADERS
        self.num_tabs = NUM_TABS
        self.headless = HEADLESS_MODE
        self.browser_timeout = BROWSER_TIMEOUT
        self.instrument_type_mapping = self._load_instrument_type_mapping()
    
    def _load_instrument_type_mapping(self) -> Dict[str, str]:
        """Load instrument type mapping from JSON file (code -> name)."""
        try:
            with open('instrument_types.json', 'r') as f:
                name_to_code = json.load(f)
            
            # Create reverse mapping (code -> name)
            code_to_name = {code: name for name, code in name_to_code.items()}
            return code_to_name
            
        except Exception as e:
            return {}
    
    def _get_instrument_type_name(self, doc_type: str) -> str:
        """Get human-readable instrument type name from code."""
        if not doc_type:
            return ''
        
        # Try to find the name for this code
        return self.instrument_type_mapping.get(doc_type, doc_type)
    
    async def perform_single_search(self, page, search_name: str) -> Optional[str]:
        """
        Perform a single HCAD property search and return address if found.
        
        Args:
            page: Playwright page object
            search_name: Name to search for
            
        Returns:
            Address if found, None otherwise
        """
        try:
            # Wait for the search input to be visible - try multiple selectors
            search_input = None
            selectors_to_try = [
                "input.searchTerm",
                "input.autocomplete",
                "input[placeholder*='Search by']",
                "input[type='search']"
            ]
            
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    search_input = page.locator(selector)
                    break
                except:
                    continue
            
            if not search_input:
                raise Exception("Could not find search input field")
            
            # Clear and fill the search input
            await search_input.clear()
            await search_input.fill(search_name)
            await asyncio.sleep(1)
            
            # Click the search button - try multiple selectors
            button_selectors = [
                "div.input-group-append button.btn.btn-primary",
                "button.btn.btn-primary:has(i.fa-search)",
                "button[type='button'].btn.btn-primary",
                ".input-group-append button"
            ]
            
            search_button = None
            for selector in button_selectors:
                try:
                    search_button = page.locator(selector)
                    if await search_button.count() > 0:
                        break
                except:
                    continue
            
            if search_button and await search_button.count() > 0:
                await search_button.first.click()
            else:
                # Try pressing Enter on the input field
                await search_input.press("Enter")
            
            await asyncio.sleep(3)

            # Check if there are any results or if we got a "no results" message
            page_content = await page.content()
            if any(indicator in page_content for indicator in NO_RESULTS_INDICATORS):
                print(f"No results message found for: '{search_name}'")
                return None
            
            # Wait for results table and extract address
            try:
                # Try different table selectors based on the HTML structure
                table_selectors = [
                    "table.data-table.dataTable tbody tr.resulttr",
                    "table.data-table tbody tr",
                    "table.dataTable tbody tr",
                    ".data-table tbody tr",
                    "table[id*='DataTable'] tbody tr",
                    "tbody tr.resulttr"
                ]
                
                # First check for "No Results Found" message immediately
                no_results_selectors = [
                    "th:has-text('No Results Found')",
                    "td:has-text('No Results Found')",
                    "div:has-text('No Results Found')",
                    "table:has-text('No Results Found')",
                    "th[colspan='4']:has-text('No Results Found')",  # Specific to the HTML structure you mentioned
                    ".card-body table th:has-text('No Results Found')"
                ]
                
                no_results_found = False
                for selector in no_results_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)  # Quick check
                        no_results_found = True
                        print(f"Found 'No Results Found' message using selector: {selector}")
                        break
                    except:
                        continue
                
                if no_results_found:
                    print("No results found for this search, skipping...")
                    return None
                
                # Additional check: Look for any element containing "No Results Found" text
                try:
                    no_results_text = await page.locator("text=No Results Found").count()
                    if no_results_text > 0:
                        print("Found 'No Results Found' text on page, skipping...")
                        return None
                except:
                    pass
                
                results_found = False
                table_selector_used = None
                for selector in table_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)  # Reduced timeout
                        results_found = True
                        table_selector_used = selector
                        print(f"Found results table using selector: {selector}")
                        break
                    except:
                        continue
                
                if results_found:
                    # Extract data from the specific columns based on the HTML structure
                    try:
                        # Address is in the 3rd column (td:nth-child(3))
                        address_element = page.locator(f"{table_selector_used}:first-child td.resulttd:nth-child(3)")
                        if await address_element.count() == 0:
                            # Fallback to simpler selector
                            address_element = page.locator("table tbody tr:first-child td:nth-child(3)")
                        
                        address = await address_element.inner_text()
                        address = address.strip() if address else None
                        
                        # Also extract other useful information
                        try:
                            account_element = page.locator(f"{table_selector_used}:first-child td.resulttd:nth-child(1)")
                            account_number = await account_element.inner_text()
                            account_number = account_number.strip() if account_number else None
                            print(f"Found account: {account_number}, address: {address}")
                        except:
                            pass
                        
                        # Return the address if found
                        return address
                            
                    except Exception as e:
                        print(f"Error extracting address from results: {e}")
                        # Fallback to any text that looks like an address
                        try:
                            all_cells = page.locator("table tbody tr:first-child td")
                            cell_count = await all_cells.count()
                            for i in range(cell_count):
                                cell_text = await all_cells.nth(i).inner_text()
                                # Look for text that contains common address patterns
                                if cell_text and any(pattern in cell_text.upper() for pattern in ADDRESS_PATTERNS):
                                    return cell_text.strip()
                        except:
                            pass
                else:
                    print(f"No results found in table for: '{search_name}'")
                    return None
                    
            except Exception as e:
                print(f"Error waiting for results table for '{search_name}': {e}")
                return None

            # Try to go back to search page for next search
            try:
                # Look for a "New Search" button or similar
                new_search_btn = page.locator("button:has-text('New Search'), a:has-text('New Search'), input[value*='Reset'], button:has-text('Reset')")
                if await new_search_btn.count() > 0:
                    await new_search_btn.first.click()
                    await asyncio.sleep(1)
                else:
                    # If no reset button, go back to main page
                    await page.goto(self.base_url)
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"Could not reset search, going back to main page: {e}")
                await page.goto(self.base_url)
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error during search for '{search_name}': {e}")

        return None
    
    async def run_search(self, page, owner_name: str, legal_desc_clean: str, legal_desc_full: str, first_run: bool = False) -> Dict[str, Any]:
        """
        Run a single HCAD property search with fallback name variations.
        
        Args:
            page: Playwright page object
            owner_name: Owner name to search for
            legal_desc_clean: Cleaned legal description
            legal_desc_full: Full legal description
            first_run: Whether this is the first run (navigates to page)
            
        Returns:
            Dictionary with search results
        """
        print(f"Running search for: {owner_name}, {legal_desc_clean}, {legal_desc_full}")
        
        if first_run:
            await page.goto(self.base_url)
            await asyncio.sleep(2)
        
        # Generate name variations for fallback searches
        name_variations = generate_name_variations(owner_name)
        print(f"Name variations to try: {name_variations}")
        
        address = None
        successful_name = None
        
        # Try each name variation until we find results
        for attempt, search_name in enumerate(name_variations):
            print(f"Attempt {attempt + 1}: Searching for '{search_name}'")
            
            result = await self.perform_single_search(page, search_name)
            
            if result:  # If we found an address
                address = result
                successful_name = search_name
                print(f"✓ Found result with name variation: '{search_name}' -> {address}")
                break
            else:
                print(f"✗ No results for: '{search_name}'")
                if attempt < len(name_variations) - 1:  # Not the last attempt
                    print(f"Trying next variation...")
                    await asyncio.sleep(1)
        
        return {
            "owner": owner_name,
            "successful_search_name": successful_name,
            "desc_clean": legal_desc_clean,
            "desc_full": legal_desc_full,
            "address": address,
        }
    
    async def worker(self, page, queue: asyncio.Queue, results: List[Dict]) -> None:
        """
        Worker function for processing search queue.
        
        Args:
            page: Playwright page object
            queue: Queue of search tasks
            results: List to store results
        """
        first_run = True
        while not queue.empty():
            row = await queue.get()
            owner = extract_owner_name(row.get("Grantees", ""))
            legal_desc_full = str(row.get("LegalDescription", "")).strip()
            legal_desc_clean = clean_legal_description(legal_desc_full)

            result = await self.run_search(page, owner, legal_desc_clean, legal_desc_full, first_run=first_run)

            # Create standardized result format to match Step 2
            # Get instrument type name from code
            doc_type_code = row.get('DocType', '')
            instrument_type_name = self._get_instrument_type_name(doc_type_code)
            
            # Debug: Log if DocType is missing
            if not doc_type_code:
                logger.warning(f"Missing DocType in HCAD record: {row.keys()}")
            
            standardized_result = {
                'FileNo': row.get('FileNo', ''),
                'Grantor': row.get('Grantors', ''),
                'Grantee': row.get('Grantees', ''),
                'Instrument Type': instrument_type_name,
                'Recording Date': row.get('FileDate', ''),
                'Film Code': row.get('FilmCode', ''),
                'Legal Description': row.get('LegalDescription', ''),
                'Property Address': result["address"] or ''
            }

            results.append(standardized_result)

            first_run = False
            queue.task_done()
    
    async def run_hcad_searches(self, df: pd.DataFrame) -> None:
        """
        Run HCAD searches for all rows in the DataFrame.
        
        Args:
            df: DataFrame with instrument data
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(extra_http_headers=self.browser_headers)
            tabs = [await context.new_page() for _ in range(self.num_tabs)]
            queue = asyncio.Queue()
            
            for _, row in df.iterrows():
                await queue.put(row.to_dict())  # put full row as dict

            results = []
            tasks = [asyncio.create_task(self.worker(tab, queue, results)) for tab in tabs]
            await queue.join()
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)
            
            await browser.close()
            
            # Store results in session state
            if results:
                import streamlit as st
                st.session_state.hcad_results = pd.DataFrame(results)


async def run_hcad_searches(df: pd.DataFrame) -> None:
    """
    Entry point for running HCAD searches from UI.
    
    Args:
        df: DataFrame with instrument data
    """
    scraper = HCADScraper()
    await scraper.run_hcad_searches(df)
