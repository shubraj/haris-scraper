#!/usr/bin/env python3
"""
CLI tool to extract addresses from text using OpenAI.
Usage: python extract_addresses.py "text with addresses"
"""
import sys
import os
from utils.address_extractor import extract_addresses_from_text, AddressExtractor


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python extract_addresses.py \"text with addresses\"")
        print("Example: python extract_addresses.py \"Grantees: JOHN SMITH, 1610 Crestdale Drive, Unit 4, Houston, Harris County, Texas 77080\"")
        sys.exit(1)
    
    text = sys.argv[1]
    
    try:
        print(f"Extracting addresses from: {text[:100]}...")
        
        extractor = AddressExtractor()
        addresses = extractor.extract_addresses(text)
        
        if addresses:
            print(f"\n✅ Found {len(addresses)} address(es):")
            for i, addr in enumerate(addresses, 1):
                print(f"\n{i}. {extractor.standardize_address(addr)}")
                print(f"   Confidence: {addr.get('confidence', 'unknown')}")
                print(f"   Street: {addr.get('street_number', '')} {addr.get('street_name', '')}")
                print(f"   City: {addr.get('city', '')}")
                print(f"   State: {addr.get('state', '')}")
                print(f"   ZIP: {addr.get('zip_code', '')}")
        else:
            print("❌ No addresses found in the text")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure to set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)


if __name__ == "__main__":
    main()
