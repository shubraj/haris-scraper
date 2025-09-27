import re
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

NUM_TABS = 5


def clean_legal_desc(text: str) -> str:
    """Clean up legal description text."""
    if not isinstance(text, str):
        return ""
    if not text.strip().lower().startswith("desc:"):
        return ""
    desc = text.split("Desc:", 1)[1].strip()
    desc = re.sub(r"\b(ADDITION|SUBDIVISION)\b", "", desc, flags=re.IGNORECASE)
    stop_keywords = ["Sec:", "Lot:", "Block:", "Unit:", "Abstract:"]
    for kw in stop_keywords:
        idx = desc.lower().find(kw.lower())
        if idx != -1:
            desc = desc[:idx]
            break
    return desc.strip()


def remove_duplicate_letters(name: str) -> str:
    """Remove subsequent duplicate letters from a name."""
    if not name:
        return name
    
    result = []
    prev_char = None
    
    for char in name:
        if char != prev_char:
            result.append(char)
        elif char.isalpha():  # Only remove duplicate letters, keep spaces and other chars
            continue
        else:
            result.append(char)
        prev_char = char
    
    return ''.join(result)


def generate_name_variations(owner_name: str) -> list:
    """Generate variations of the owner name for fallback searches."""
    # If LLC, only use the original name
    if 'llc' in owner_name.lower():
        return [owner_name]

    import string
    # Replace punctuation with space
    punct_to_space = owner_name.translate(str.maketrans({p: ' ' for p in string.punctuation}))
    variants = [owner_name]
    if punct_to_space != owner_name:
        variants.append(' '.join(punct_to_space.split()))  # collapse multiple spaces

    words = punct_to_space.split()
    if len(words) == 2:
        w1, w2 = words
        v2 = f"{w1} {remove_duplicate_letters(w2)}"
        v3 = f"{remove_duplicate_letters(w1)} {w2}"
        v4 = f"{remove_duplicate_letters(w1)} {remove_duplicate_letters(w2)}"
        for var in [v2, v3, v4]:
            if var not in variants:
                variants.append(var)
    else:
        # For other cases, just add fully deduped
        dedup = ' '.join(remove_duplicate_letters(word) for word in words)
        if dedup != punct_to_space and dedup not in variants:
            variants.append(dedup)
    # Remove duplicates while preserving order
    unique_variations = []
    for var in variants:
        if var not in unique_variations:
            unique_variations.append(var)
    return unique_variations


async def run_search(page, owner_name, legal_desc_clean, legal_desc_full, first_run=False):
    """Run a single HCAD property search with fallback name variations."""
    print(f"Running search for: {owner_name}, {legal_desc_clean}, {legal_desc_full}")
    if first_run:
        await page.goto("https://search.hcad.org/")
        await asyncio.sleep(2)
    
    # Generate name variations for fallback searches
    name_variations = generate_name_variations(owner_name)
    print(f"Name variations to try: {name_variations}")
    
    address = None
    successful_name = None
    
    # Try each name variation until we find results
    for attempt, search_name in enumerate(name_variations):
        print(f"Attempt {attempt + 1}: Searching for '{search_name}'")
        
        result = await perform_single_search(page, search_name)
        
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


async def perform_single_search(page, search_name):
    """Perform a single search attempt and return address if found."""

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
        no_results_indicators = [
            "No results found",
            "0 entries",
            "Showing 0 to 0 of 0 entries",
            "No matching records found"
        ]
        
        page_content = await page.content()
        if any(indicator in page_content for indicator in no_results_indicators):
            print(f"No results message found for: '{search_name}'")
            address = None
        else:
            # Wait for results table and extract address
            try:
                # Try different table selectors based on the HTML structure you provided
                table_selectors = [
                    "table.data-table.dataTable tbody tr.resulttr",
                    "table.data-table tbody tr",
                    "table.dataTable tbody tr",
                    ".data-table tbody tr",
                    "table[id*='DataTable'] tbody tr",
                    "tbody tr.resulttr"
                ]
                
                results_found = False
                table_selector_used = None
                for selector in table_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=10000)
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
                                if cell_text and any(pattern in cell_text.upper() for pattern in ['ST', 'AVE', 'RD', 'DR', 'LN', 'BLVD', 'TX', 'KATY', 'HOUSTON']):
                                    return cell_text.strip()
                        except:
                            pass
                else:
                    print(f"No results found in table for: '{search_name}'")
                    address = None
                    
            except Exception as e:
                print(f"Error waiting for results table for '{search_name}': {e}")
                address = None

        # Try to go back to search page for next search
        try:
            # Look for a "New Search" button or similar
            new_search_btn = page.locator("button:has-text('New Search'), a:has-text('New Search'), input[value*='Reset'], button:has-text('Reset')")
            if await new_search_btn.count() > 0:
                await new_search_btn.first.click()
                await asyncio.sleep(1)
            else:
                # If no reset button, go back to main page
                await page.goto("https://search.hcad.org/")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Could not reset search, going back to main page: {e}")
            await page.goto("https://search.hcad.org/")
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error during search for '{search_name}': {e}")

    return None


async def worker(page, queue, results, results_placeholder):
    first_run = True
    while not queue.empty():
        row = await queue.get()
        owner = str(row.get("Grantees", "")).split(",")[0].strip()
        legal_desc_full = str(row.get("LegalDescription", "")).strip()
        legal_desc_clean = clean_legal_desc(legal_desc_full)

        result = await run_search(page, owner, legal_desc_clean, legal_desc_full, first_run=first_run)

        # Copy original row and add Address
        row_with_address = row.copy()
        row_with_address["Address"] = result["address"]

        results.append(row_with_address)
        results_placeholder.dataframe(pd.DataFrame(results))

        first_run = False
        queue.task_done()


async def main_async(df, results_placeholder):
    # Fill queue with full rows
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
                    extra_http_headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/139.0.0.0 Safari/537.36",
                        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,fr;q=0.7",
                        "Accept": "*/*",
                        "X-Requested-With": "XMLHttpRequest",
                    }
                )
        tabs = [await context.new_page() for _ in range(NUM_TABS)]
        queue = asyncio.Queue()
        for _, row in df.iterrows():
            await queue.put(row.to_dict())  # put full row as dict

        results = []
        tasks = [asyncio.create_task(worker(tab, queue, results, results_placeholder)) for tab in tabs]
        await queue.join()
        await asyncio.gather(*tasks)
        await asyncio.sleep(2)



async def run_hcad_searches(df: pd.DataFrame):
    """Entry point for running HCAD searches from UI."""
    import streamlit as st
    results_placeholder = st.empty()
    await main_async(df, results_placeholder)
