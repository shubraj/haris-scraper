#!/usr/bin/env python3
"""
Example of using session state with the Harris County scraper and address extractor.
This shows how to properly use session state in Streamlit applications.
"""
import streamlit as st
from scrapers.harris_county_scraper import HarrisCountyScraper
from utils.address_extractor import AddressExtractor


def init_session_state():
    """Initialize all session state variables."""
    if "harris_scraper" not in st.session_state:
        st.session_state.harris_scraper = HarrisCountyScraper()
    
    if "address_extractor" not in st.session_state:
        st.session_state.address_extractor = AddressExtractor()
    
    if "scraped_data" not in st.session_state:
        st.session_state.scraped_data = None
    
    if "extracted_addresses" not in st.session_state:
        st.session_state.extracted_addresses = []


def main():
    """Example Streamlit app using session state."""
    st.title("Session State Example")
    
    # Initialize session state
    init_session_state()
    
    # Get instances from session state
    scraper = st.session_state.harris_scraper
    address_extractor = st.session_state.address_extractor
    
    st.write("### Scraper Info")
    info = scraper.get_scraper_info()
    st.json(info)
    
    st.write("### Address Extraction Test")
    sample_text = "Grantees: JOHN SMITH, 1610 Crestdale Drive, Unit 4, Houston, Harris County, Texas 77080"
    
    if st.button("Extract Addresses"):
        addresses = address_extractor.extract_grantees_addresses_only(sample_text)
        st.session_state.extracted_addresses = addresses
        
        for i, addr in enumerate(addresses, 1):
            st.write(f"{i}. {address_extractor.standardize_address(addr)}")
    
    if st.session_state.extracted_addresses:
        st.write("### Extracted Addresses")
        for addr in st.session_state.extracted_addresses:
            st.write(f"- {address_extractor.standardize_address(addr)}")


if __name__ == "__main__":
    main()
