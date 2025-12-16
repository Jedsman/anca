from tools.ebay_tool import EbayTool
import logging

# Configure logger to print to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EbayTool")

def test_search():
    tool = EbayTool()
    print("Testing Keyword Search...")
    # Search for something common
    items = tool.find_active_auctions(keywords="camera", max_results=5)
    
    for item in items:
        # We need to inspect the RAW item to see buyingOptions, but find_active_auctions stores it in 'raw_rest'
        raw = item.get('raw_rest', {})
        options = raw.get('buyingOptions', [])
        print(f"Item: {item['title'][:30]}... | Options: {options} | Bids: {item['sellingStatus']['bidCount']}")

if __name__ == "__main__":
    test_search()
