"""
Text processing utilities for cleaning and normalizing data.
"""
import re
import string
from typing import List, Optional


def clean_legal_description(text: str) -> str:
    """
    Clean up legal description text by removing unnecessary keywords and formatting.
    
    Args:
        text: Raw legal description text
        
    Returns:
        Cleaned legal description text
    """
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
    """
    Remove subsequent duplicate letters from a name while preserving spaces and punctuation.
    
    Args:
        name: Input name string
        
    Returns:
        Name with duplicate letters removed
    """
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


def generate_name_variations(owner_name: str) -> List[str]:
    """
    Generate variations of the owner name for fallback searches.
    
    Args:
        owner_name: Original owner name
        
    Returns:
        List of name variations to try
    """
    # If LLC, only use the original name
    if 'llc' in owner_name.lower():
        return [owner_name]

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


def extract_owner_name(grantee_text: str) -> str:
    """
    Extract the primary owner name from grantee text.
    
    Args:
        grantee_text: Full grantee text
        
    Returns:
        Primary owner name (first part before comma)
    """
    if not grantee_text:
        return ""
    
    return str(grantee_text).split(",")[0].strip()
