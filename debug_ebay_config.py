import sys
import os
# Add current dir to path so we can import app
sys.path.append(os.getcwd())

from app.core.config_sniper import sniper_settings
from tools.ebay_tool import EbayTool

def mask(s):
    if not s: return "Not Set"
    if len(s) < 8: return s
    return s[:4] + "***" + s[-4:]

def check_config():
    print("----- eBay Sniper Configuration Check -----")
    print(f"EBAY_SANDBOX (Env/Config): {sniper_settings.ebay_sandbox}")
    print(f"EBAY_APP_ID (Config): {mask(sniper_settings.ebay_app_id)}")
    
    tool = EbayTool()
    
    # Check what logic EbayTool uses
    expected_domain = "svcs.sandbox.ebay.com" if sniper_settings.ebay_sandbox else "svcs.ebay.com"
    print(f"Expected Domain (Logic): {expected_domain}")

    connection = tool._get_connection()
    
    # Inspect connection internals safely
    if hasattr(connection, 'config'):
        print(f"Connection Config: {connection.config}")
    
    # Try to see actual endpoints if possible, or just trust the logic above + env vars
    print("------------------------------------------")

if __name__ == "__main__":
    check_config()
