import os
import requests
import base64
from app.core.config_sniper import sniper_settings

def test_oauth_and_browse():
    print("Testing eBay OAuth + Browse API (REST)...")
    
    app_id = sniper_settings.ebay_app_id
    cert_id = sniper_settings.ebay_cert_id
    
    if not app_id or not cert_id:
        print("ERROR: EBAY_APP_ID or EBAY_CERT_ID missing.")
        return

    # 1. Get OAuth Token
    # Encode 'clientId:clientSecret'
    credentials = f"{app_id}:{cert_id}"
    encoded_creds = base64.b64encode(credentials.encode()).decode()
    
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    # For Sandbox, it would be https://api.sandbox.ebay.com/identity/v1/oauth2/token
    # But user is on Prod now.
    
    headers = {
        "Authorization": f"Basic {encoded_creds}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope" # Basic public data scope
    }
    
    print(f"Requesting Token from {token_url}...")
    try:
        resp = requests.post(token_url, headers=headers, data=data)
        if resp.status_code != 200:
            print(f"Token Failed: {resp.status_code} - {resp.text}")
            return
            
        token_data = resp.json()
        access_token = token_data['access_token']
        print("SUCCESS: Got Access Token!")
        
    except Exception as e:
        print(f"Exception during auth: {e}")
        return

    # 2. Search Item (Browse API)
    search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US" 
    }
    
    params = {
        "q": "iphone cable",
        "limit": 3
    }
    
    print(f"Searching via Browse API: {search_url}")
    try:
        resp = requests.get(search_url, headers=headers, params=params)
        if resp.status_code != 200:
             print(f"Search Failed: {resp.status_code} - {resp.text}")
             return
             
        data = resp.json()
        total = data.get('total', 0)
        items = data.get('itemSummaries', [])
        print(f"SUCCESS: Found {total} items. First {len(items)}:")
        for item in items:
            print(f" - {item.get('title')} (${item.get('price', {}).get('value')})")
            
    except Exception as e:
        print(f"Exception during search: {e}")

if __name__ == "__main__":
    test_oauth_and_browse()
