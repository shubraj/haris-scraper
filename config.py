"""
Configuration settings for the Harris County Property Scraper.
"""
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Credentials from .env file
HCTX_USERNAME = os.getenv("HCTX_USERNAME", "")
HCTX_PASSWORD = os.getenv("HCTX_PASSWORD", "")

# Harris County Scraper Configuration
HARRIS_COUNTY_BASE_URL = "https://www.cclerk.hctx.net/applications/websearch/"

# HCAD Configuration
HCAD_BASE_URL = "https://search.hcad.org/"
HCAD_PROPERTY_SEARCH_URL = "https://hcad.org/property-search/property-search"

# Browser Configuration
NUM_TABS = 5
HEADLESS_MODE = True

# Request Headers
DEFAULT_HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,fr;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.cclerk.hctx.net',
    'Pragma': 'no-cache',
    'Referer': 'https://www.cclerk.hctx.net/applications/websearch/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

# Browser Headers for Playwright
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,fr;q=0.7",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
}

# File Paths
INSTRUMENT_TYPES_FILE = Path(__file__).parent / "instrument_types.json"
OUTPUT_EXCEL_FILE = Path(__file__).parent / "output.xlsx"

# Timeout Settings
REQUEST_TIMEOUT = 30
BROWSER_TIMEOUT = 10000
SEARCH_TIMEOUT = 30000

# Legal Description Cleaning Keywords
LEGAL_DESC_STOP_KEYWORDS = ["Sec:", "Lot:", "Block:", "Unit:", "Abstract:"]
LEGAL_DESC_REMOVE_KEYWORDS = ["ADDITION", "SUBDIVISION"]

# Address Patterns for HCAD Search
ADDRESS_PATTERNS = ['ST', 'AVE', 'RD', 'DR', 'LN', 'BLVD', 'TX', 'KATY', 'HOUSTON']

# No Results Indicators
NO_RESULTS_INDICATORS = [
    "No results found",
    "0 entries",
    "Showing 0 to 0 of 0 entries",
    "No matching records found"
]
