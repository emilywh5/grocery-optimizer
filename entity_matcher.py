from rapidfuzz import fuzz, process

DEFAULT_THRESHOLD = 75.0

def normalize_text(text: str) -> str:
    """
    Normalizes text to handle case-sensitivity and basic singular/plural issues
    """
    text = text.lower().strip()
    words = [word[:-1] if word.endswith('s') and len(word) > 3 else word for word in text.split()]
    return " ".join(words)

def resolve_product(raw_name: str, master_catalog: list, threshold: float = DEFAULT_THRESHOLD) -> str:
    """
    Fuzzy matches a messy raw product string to a standardized master catalog key.
    
    Args:
        raw_name (str): The messy product name scraped from a store.
        master_catalog (list): Clean, standard target keys (ex. ['milk', 'tofu']).
        threshold (float): Minimum confidence similarity score (0-100) to accept a match.
        
    Returns:
        str: The matched master key if successful, or None if the match is too weak.
    """
    norm_scraped = normalize_text(raw_name)
    
    normalized_master = {normalize_text(key): key for key in master_catalog}
    
    best_match_info = process.extractOne(
        norm_scraped, 
        list(normalized_master.keys()), 
        scorer=fuzz.partial_ratio
    )
    
    if best_match_info:
        matched_norm_key, score, _ = best_match_info
        if score >= threshold:
            return normalized_master[matched_norm_key]
            
    return None

# TEST BLOCK
if __name__ == "__main__":
    TEST_MASTER_PRODUCTS = ["milk", "eggs", "bread", "bananas", "tofu"]
    TEST_SCRAPED_INPUTS = [
        "Banana Conventional, 1 Each",
        "Grade A Large White Eggs - 12ct",
        "Organic Tofu",
        "Roundy's Select 2% Reduced Fat Milk",
        "365 by Whole Foods Market Organic Whole Wheat Bread, 20 OZ",
        "Doritos Nacho Cheese Chips"
    ]

    mapped_items = {}
    unmapped_items = []
    confidence_threshold = 65.0

    print("Running Entity Resolution Test Suite")
    print("-" * 60)

    for scraped_item in TEST_SCRAPED_INPUTS:
        match = resolve_product(scraped_item, TEST_MASTER_PRODUCTS, confidence_threshold)
        
        if match:
            mapped_items[scraped_item] = match
            print(f"MATCHED: '{scraped_item}' -> [{match.upper()}]")
        else:
            unmapped_items.append(scraped_item)
            print(f"REJECTED: '{scraped_item}'")
        print("-" * 60)

    print("\nFINAL INGESTION SUMMARY")
    print(f"Successfully Mapped: {len(mapped_items)} items")
    print(f"Sent to Manual Review: {len(unmapped_items)} items")