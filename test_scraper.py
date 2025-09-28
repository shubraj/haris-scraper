#!/usr/bin/env python3
"""
Test script for the class-based Harris County scraper.
"""
from scrapers.harris_county_scraper import HarrisCountyScraper
import pandas as pd


def test_scraper():
    """Test the Harris County scraper."""
    print("🧪 Testing Harris County Scraper")
    print("=" * 50)
    
    # Initialize scraper
    scraper = HarrisCountyScraper()
    
    # Test scraper info
    info = scraper.get_scraper_info()
    print(f"📋 Scraper Info: {info['name']} v{info['version']}")
    print(f"🌐 Base URL: {info['base_url']}")
    print(f"⏱️  Timeout: {info['timeout']}s")
    print()
    
    # Test date validation
    print("📅 Testing date validation:")
    valid_dates = ["01/01/2025", "12/31/2025", "06/15/2025"]
    invalid_dates = ["2025-01-01", "1/1/25", "invalid"]
    
    for date_str in valid_dates:
        is_valid = scraper.validate_date_format(date_str)
        print(f"  ✅ {date_str}: {'Valid' if is_valid else 'Invalid'}")
    
    for date_str in invalid_dates:
        is_valid = scraper.validate_date_format(date_str)
        print(f"  ❌ {date_str}: {'Valid' if is_valid else 'Invalid'}")
    print()
    
    # Test available instrument types
    print("📋 Available instrument types:")
    types = scraper.get_available_instrument_types()
    for i, inst_type in enumerate(types[:5], 1):  # Show first 5
        print(f"  {i}. {inst_type}")
    print(f"  ... and {len(types) - 5} more" if len(types) > 5 else "")
    print()
    
    # Test a small scrape (if you want to test actual scraping)
    print("🔍 Testing actual scraping (DEED records from recent dates):")
    try:
        df = scraper.scrape_records("DEED", "01/01/2025", "01/02/2025")
        
        if not df.empty:
            print(f"  ✅ Successfully scraped {len(df)} records")
            print(f"  📊 Columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"  📄 Sample record:")
                sample = df.iloc[0]
                for col in ['FileNo', 'FileDate', 'DocType', 'Grantors', 'Grantees']:
                    if col in sample:
                        print(f"    {col}: {sample[col]}")
        else:
            print("  ℹ️  No records found (this is normal for recent dates)")
            
    except Exception as e:
        print(f"  ❌ Error during scraping: {e}")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_scraper()
