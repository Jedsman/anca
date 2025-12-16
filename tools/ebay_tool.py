import requests
import base64
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config_sniper import sniper_settings
from app.core.logging_sniper import get_sniper_logger

logger = get_sniper_logger("EbayTool")

class RateLimiter:
    """Simple rate limiter for eBay API calls."""
    def __init__(self, max_calls_per_day: int = 5000):
        self.max_calls_per_day = max_calls_per_day
        self.calls_today = 0
        self.reset_time = datetime.now() + timedelta(days=1)
        self.reset_time = self.reset_time.replace(hour=0, minute=0, second=0, microsecond=0)

    def check_and_increment(self) -> bool:
        """Check if we can make another API call and increment counter."""
        # Reset counter if it's a new day
        if datetime.now() >= self.reset_time:
            self.calls_today = 0
            self.reset_time = datetime.now() + timedelta(days=1)
            self.reset_time = self.reset_time.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info("[RATE LIMIT] Daily counter reset")

        if self.calls_today >= self.max_calls_per_day:
            logger.warning(f"[RATE LIMIT] Daily limit reached: {self.calls_today}/{self.max_calls_per_day}")
            return False

        self.calls_today += 1
        return True

    def get_remaining_calls(self) -> int:
        """Get remaining API calls for today."""
        return max(0, self.max_calls_per_day - self.calls_today)

class EbayTool:
    """
    Wrapper for eBay Browse API (REST).
    Replaces legacy ebaysdk (XML) due to permission/quota issues.
    """
    # Class-level rate limiter shared across instances
    _rate_limiter = RateLimiter(max_calls_per_day=5000)

    def __init__(self):
        self.appid = sniper_settings.ebay_app_id
        self.certid = sniper_settings.ebay_cert_id
        self.token = None
        self.token_expiry = 0

        if not self.appid or not self.certid:
             logger.warning("EBAY_APP_ID or EBAY_CERT_ID is not set!")

    @classmethod
    def get_rate_limit_status(cls) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            "calls_today": cls._rate_limiter.calls_today,
            "max_calls_per_day": cls._rate_limiter.max_calls_per_day,
            "remaining_calls": cls._rate_limiter.get_remaining_calls(),
            "reset_time": cls._rate_limiter.reset_time.isoformat()
        }

    def _make_request_with_retry(self, url: str, headers: Dict[str, str], params: Dict[str, Any] = None,
                                  max_retries: int = 3, initial_delay: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP request with exponential backoff retry logic.

        Args:
            url: The URL to request
            headers: Request headers
            params: Query parameters
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            JSON response as dict, or None if all retries failed
        """
        delay = initial_delay

        for attempt in range(max_retries + 1):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=10)

                # Success
                if resp.status_code == 200:
                    return resp.json()

                # Rate limit exceeded (429) - wait longer
                if resp.status_code == 429:
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit (429). Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit hit (429). Max retries exceeded.")
                        return None

                # Server errors (5xx) - retry
                if 500 <= resp.status_code < 600:
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Server error ({resp.status_code}). Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Server error ({resp.status_code}). Max retries exceeded: {resp.text}")
                        return None

                # Client errors (4xx except 429) - don't retry
                if 400 <= resp.status_code < 500:
                    logger.error(f"Client error ({resp.status_code}): {resp.text}")
                    return None

                # Other errors
                logger.error(f"Unexpected status code ({resp.status_code}): {resp.text}")
                return None

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Request timeout. Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Request timeout. Max retries exceeded.")
                    return None

            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Request exception: {e}. Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request exception: {e}. Max retries exceeded.")
                    return None

        return None

    def _get_token(self) -> Optional[str]:
        """
        Get or refresh OAuth Client Credentials token.
        """
        if self.token and time.time() < self.token_expiry:
            return self.token

        try:
            credentials = f"{self.appid}:{self.certid}"
            encoded_creds = base64.b64encode(credentials.encode()).decode()
            
            # TODO: Handle Sandbox vs Prod URL if needed. 
            # For now assuming Prod based on user's success.
            token_url = "https://api.ebay.com/identity/v1/oauth2/token"
            if sniper_settings.ebay_sandbox:
                 token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

            headers = {
                "Authorization": f"Basic {encoded_creds}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
            
            resp = requests.post(token_url, headers=headers, data=data, timeout=10)
            if resp.status_code != 200:
                logger.error(f"OAuth Failed: {resp.status_code} - {resp.text}")
                return None
                
            token_data = resp.json()
            self.token = token_data['access_token']
            # expires_in is seconds, buffer by 60s
            self.token_expiry = time.time() + int(token_data.get('expires_in', 7200)) - 60
            return self.token
            
        except Exception as e:
            logger.error(f"OAuth Exception: {e}")
            return None

    def find_active_auctions(self, keywords: str = None, category_ids: str = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for active listings using Browse API.
        Can use 'keywords' OR 'category_ids' (or both).
        """
        # If no input, return empty to be safe
        if not keywords and not category_ids:
             return []

        if sniper_settings.mock_ebay:
             logger.info(f"[MOCK] Returning items for {keywords or category_ids}")
             from app.core.constants import MOCK_LISTINGS
             return MOCK_LISTINGS

        # Check rate limit before making API call
        if not self._rate_limiter.check_and_increment():
            remaining = self._rate_limiter.get_remaining_calls()
            logger.error(f"[RATE LIMIT] Cannot make API call. {remaining} calls remaining today.")
            return []

        token = self._get_token()
        if not token:
            logger.error("Cannot search without token.")
            return []

        search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        if sniper_settings.ebay_sandbox:
             search_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB" 
        }
        
        params = {
            "limit": max_results, 
            "sort": "endingSoonest", 
            "filter": "buyingOptions:{AUCTION}" 
        }
        
        if keywords:
            params["q"] = keywords

        if category_ids:
            params["category_ids"] = category_ids
            logger.info(f"Searching eBay Category {category_ids}...")
        else:
            logger.info(f"Searching eBay Keywords: {keywords}...")

        # Use retry logic for API call
        try:
            data = self._make_request_with_retry(search_url, headers, params)
            if data is None:
                logger.error("Search failed after retries")
                return []

            items = data.get('itemSummaries', [])
            
            # Normalize to match our internal expectation (similar to XML structure but simplified)
            normalized_items = []
            for item in items:
                # Extract pricing
                price_val = 0.0
                try:
                    price_val = float(item.get('price', {}).get('value', 0))
                except: pass
                
                # Extract bids if available (Browse API sometimes hides this in item_summary, depends on fields)
                # 'bidCount' is often a field in itemSummary
                bid_count = item.get('bidCount', 0)
                
                # Filter locally for low bids if API didn't do strict check (REST filter for bid count is complex)
                if int(bid_count) > 2:
                    continue 

                normalized = {
                    'itemId': item.get('itemId'), # Legacy ID often inside here
                    'title': item.get('title'),
                    'imageUrl': item.get('image', {}).get('imageUrl'),
                    'viewItemURL': item.get('itemWebUrl'),
                    'sellingStatus': {
                        'currentPrice': {'value': price_val},
                        'bidCount': bid_count,
                        'timeLeft': "Determined by sort" # REST doesn't always give simple ISO duration here
                    },
                    'listingInfo': {
                        'watchCount': item.get('watchCount', 0)
                    },
                    'condition': {
                        'conditionDisplayName': item.get('condition')
                    },
                    # Add raw just in case
                    'raw_rest': item
                }
                normalized_items.append(normalized)
            
            logger.info(f"Found {len(items)} items, kept {len(normalized_items)} after filtering.")
            return normalized_items

        except Exception as e:
            logger.error(f"Search Exception: {e}")
            return []
            
    def find_completed_items(self, keywords: str, condition_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find completed listings to determine market value (Sold items).
        REST API NOTE: Browse API does not easily expose Sold items without Marketplace Insights (restricted).
        For MVP, we will return an empty list or mock to avoid crashing.
        """
        # TODO: Implement MarketPlace Insights API or scrape approach if needed later.
        if sniper_settings.mock_ebay or (keywords and keywords.startswith("MOCK")):
             from app.core.constants import MOCK_COMPLETED
             return MOCK_COMPLETED

        logger.warning(f"find_completed_items called for '{keywords}'. Browse API does not support Sold items easily. Returning empty.")
        return []

    def find_lowest_bin(self, keywords: str, condition_id: str = None, limit: int = 20) -> float:
        """
        Find the lowest Buy It Now (fixed price) listing for the given keywords.
        This is used as a fallback when sold history is not available.

        Returns:
            float: Lowest BIN price found, or 0.0 if no listings found
        """
        if sniper_settings.mock_ebay or (keywords and keywords.startswith("MOCK")):
            logger.info(f"[MOCK] Returning mock BIN price for {keywords}")
            # Return a reasonable mock price
            return 150.0

        # Check rate limit before making API call
        if not self._rate_limiter.check_and_increment():
            remaining = self._rate_limiter.get_remaining_calls()
            logger.error(f"[RATE LIMIT] Cannot make BIN search. {remaining} calls remaining today.")
            return 0.0

        token = self._get_token()
        if not token:
            logger.error("Cannot search BIN without token.")
            return 0.0

        search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        if sniper_settings.ebay_sandbox:
            search_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
        }

        # Search for Buy It Now (fixed price) listings, sorted by price ascending
        params = {
            "q": keywords,
            "limit": limit,
            "sort": "price",  # Sort by price ascending to get lowest first
            "filter": "buyingOptions:{FIXED_PRICE}"  # Only fixed price listings
        }

        try:
            logger.info(f"Searching eBay for lowest BIN: {keywords}")

            # Use retry logic for API call
            data = self._make_request_with_retry(search_url, headers, params)
            if data is None:
                logger.error("BIN search failed after retries")
                return 0.0

            items = data.get('itemSummaries', [])

            if not items:
                logger.info(f"No BIN listings found for: {keywords}")
                return 0.0

            # Extract prices and find the minimum
            prices = []
            for item in items:
                try:
                    price_val = float(item.get('price', {}).get('value', 0))
                    if price_val > 0:
                        prices.append(price_val)
                except (ValueError, TypeError):
                    continue

            if not prices:
                logger.info(f"No valid prices found in BIN listings for: {keywords}")
                return 0.0

            lowest_price = min(prices)
            logger.info(f"Lowest BIN for '{keywords[:30]}...': ${lowest_price:.2f} (from {len(prices)} listings)")
            return lowest_price

        except Exception as e:
            logger.error(f"BIN Search Exception: {e}")
            return 0.0
