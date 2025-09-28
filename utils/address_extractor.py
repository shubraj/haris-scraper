"""
OpenAI-powered address extraction utility.
"""
import os
import re
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import logging
from config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AddressExtractor:
    """OpenAI-powered utility for extracting addresses from text."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the address extractor.
        
        Args:
            api_key: OpenAI API key (if not provided, will use config or environment variable)
        """
        self.api_key = api_key or OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("Address extractor initialized with OpenAI API")
    
    def extract_addresses(self, text: str, context: str = "legal document") -> List[Dict[str, str]]:
        """
        Extract addresses from text using OpenAI.
        
        Args:
            text: Text to extract addresses from
            context: Context of the text (e.g., "legal document", "property record")
            
        Returns:
            List of dictionaries with extracted address information
        """
        try:
            prompt = self._create_extraction_prompt(text, context)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            addresses = self._parse_response(result)
            
            logger.info(f"Extracted {len(addresses)} addresses from text")
            return addresses
            
        except Exception as e:
            logger.error(f"Error extracting addresses: {e}")
            return []
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for address extraction."""
        return """You are an expert at extracting GRANTEES addresses from legal documents and property records. 

Your task is to:
1. ONLY extract addresses that belong to GRANTEES (property owners/recipients)
2. IGNORE addresses in legal descriptions, mailing addresses, or other non-grantee addresses
3. Look for addresses that follow Grantees names or are clearly associated with property ownership
4. Focus on residential/property addresses, not business mailing addresses
5. Look for patterns like: "JOHN SMITH, 123 Main St, Houston, TX 77001" or "ABC LLC, 1610 Crestdale Drive, Unit 4, Houston, Harris County, Texas 77080"

IMPORTANT: Only extract addresses that are clearly associated with Grantees/property owners. Ignore:
- Legal description addresses (Lot X, Block Y)
- Mailing addresses of companies
- Property addresses in legal descriptions
- Any address not directly associated with a Grantee name

Return the results in JSON format with this structure:
{
  "addresses": [
    {
      "full_address": "Complete address as found",
      "street_number": "123",
      "street_name": "Main Street",
      "unit": "Unit 4 (if applicable)",
      "city": "Houston",
      "county": "Harris County (if mentioned)",
      "state": "Texas",
      "zip_code": "77080",
      "confidence": "high/medium/low",
      "grantee_name": "Name of the grantee (if identifiable)"
    }
  ]
}

If no GRANTEES addresses are found, return: {"addresses": []}"""
    
    def _create_extraction_prompt(self, text: str, context: str) -> str:
        """Create the extraction prompt for OpenAI."""
        return f"""Extract ONLY GRANTEES addresses from the following {context} text. 

IMPORTANT: Only extract addresses that belong to Grantees (property owners). Ignore:
- Legal description addresses (Lot X, Block Y, etc.)
- Mailing addresses of companies
- Property addresses in legal descriptions
- Any address not directly associated with a Grantee name

Text to analyze:
{text}

Please extract only GRANTEES addresses and return them in the specified JSON format."""
    
    def _parse_response(self, response: str) -> List[Dict[str, str]]:
        """Parse the OpenAI response and extract addresses."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data.get('addresses', [])
            else:
                # Fallback: try to parse the entire response as JSON
                data = json.loads(response)
                return data.get('addresses', [])
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response was: {response}")
            return []
    
    def extract_from_grantees(self, grantees_text: str) -> List[Dict[str, str]]:
        """
        Extract addresses specifically from Grantees field text.
        
        Args:
            grantees_text: Text from the Grantees field
            
        Returns:
            List of extracted addresses
        """
        return self.extract_addresses(grantees_text, "grantees field")
    
    def extract_grantees_addresses_only(self, text: str) -> List[Dict[str, str]]:
        """
        Extract ONLY Grantees addresses from any text, ignoring other addresses.
        
        Args:
            text: Text that may contain various types of addresses
            
        Returns:
            List of Grantees addresses only
        """
        return self.extract_addresses(text, "grantees addresses only")
    
    def extract_from_legal_description(self, legal_desc: str) -> List[Dict[str, str]]:
        """
        Extract addresses from legal description text.
        
        Args:
            legal_desc: Legal description text
            
        Returns:
            List of extracted addresses
        """
        return self.extract_addresses(legal_desc, "legal description")
    
    def standardize_address(self, address_dict: Dict[str, str]) -> str:
        """
        Convert extracted address dictionary to standardized string format.
        
        Args:
            address_dict: Address dictionary from extraction
            
        Returns:
            Standardized address string
        """
        parts = []
        
        # Street address
        if address_dict.get('street_number') and address_dict.get('street_name'):
            street = f"{address_dict['street_number']} {address_dict['street_name']}"
            if address_dict.get('unit'):
                street += f", {address_dict['unit']}"
            parts.append(street)
        
        # City
        if address_dict.get('city'):
            parts.append(address_dict['city'])
        
        # County (if present)
        if address_dict.get('county'):
            parts.append(address_dict['county'])
        
        # State
        if address_dict.get('state'):
            parts.append(address_dict['state'])
        
        # ZIP code
        if address_dict.get('zip_code'):
            parts.append(address_dict['zip_code'])
        
        return ", ".join(parts)
    
    def batch_extract_addresses(self, texts: List[str], context: str = "legal document") -> List[List[Dict[str, str]]]:
        """
        Extract addresses from multiple texts in batch.
        
        Args:
            texts: List of texts to process
            context: Context for the texts
            
        Returns:
            List of address lists (one for each input text)
        """
        results = []
        for i, text in enumerate(texts):
            logger.info(f"Processing text {i+1}/{len(texts)}")
            addresses = self.extract_addresses(text, context)
            results.append(addresses)
        return results


def get_address_extractor(api_key: Optional[str] = None) -> AddressExtractor:
    """
    Get address extractor instance (for use with session state).
    
    Args:
        api_key: OpenAI API key (optional)
        
    Returns:
        AddressExtractor instance
    """
    return AddressExtractor(api_key)


def extract_addresses_from_text(text: str, api_key: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Convenience function to extract addresses from text.
    
    Args:
        text: Text to extract addresses from
        api_key: OpenAI API key (optional)
        
    Returns:
        List of extracted addresses
    """
    extractor = AddressExtractor(api_key)
    return extractor.extract_addresses(text)


def extract_addresses_from_grantees(grantees_text: str, api_key: Optional[str] = None) -> List[str]:
    """
    Convenience function to extract and standardize addresses from Grantees text.
    
    Args:
        grantees_text: Grantees field text
        api_key: OpenAI API key (optional)
        
    Returns:
        List of standardized address strings
    """
    extractor = AddressExtractor(api_key)
    addresses = extractor.extract_from_grantees(grantees_text)
    return [extractor.standardize_address(addr) for addr in addresses]


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Grantees: JOHN SMITH, 1610 Crestdale Drive, Unit 4, Houston, Harris County, Texas 77080
    Legal Description: Lot 1, Block 2, 123 Main Street, Houston, TX 77001
    """
    
    try:
        extractor = AddressExtractor()
        addresses = extractor.extract_addresses(sample_text)
        
        print("Extracted addresses:")
        for addr in addresses:
            print(f"- {extractor.standardize_address(addr)}")
            print(f"  Confidence: {addr.get('confidence', 'unknown')}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set OPENAI_API_KEY environment variable")
