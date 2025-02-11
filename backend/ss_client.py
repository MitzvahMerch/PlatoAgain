import os
import base64
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class SSClient:
    def __init__(self, username: str, api_key: str):
        self.base_url = "https://api.ssactivewear.com/v2"
        auth_str = f"{username}:{api_key}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        })

    def _make_request(self, params: Dict = None) -> Optional[Dict]:
        """Make request to S&S API with error handling"""
        try:
            url = f"{self.base_url}/products/"
            logger.debug(f"Making request to {url} with params: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Full URL called: {response.url}")
            
            if response.status_code != 200:
                logger.error(f"API error: Status {response.status_code}, Response: {response.text}")
                return None
                
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            logger.exception(e)
            return None

    def get_price(self, style: str, color: str) -> Optional[float]:
        """Get price for a specific style and color"""
        try:
            # Convert G640 to 64000 if needed
            if style.upper() == 'G640':
                style = '64000'
            
            params = {
                "style": f"Gildan {style}",
                "fields": "colorName,customerPrice"
            }
            
            response = self._make_request(params)
            if not response:
                return None

            # Look for matching color variant
            for variant in response:
                if variant.get('colorName') == color:
                    return variant.get('customerPrice')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting price: {str(e)}")
            return None

    def check_inventory(self, style: str, color: str) -> Optional[Dict]:
        """Check inventory levels for a specific product variant"""
        try:
            # Convert G640 to 64000 if needed
            if style.upper() == 'G640':
                style = '64000'
            
            params = {
                "style": f"Gildan {style}",
                "fields": "colorName,inventory"
            }
            
            response = self._make_request(params)
            if not response:
                return None

            # Find the matching color variant
            for variant in response:
                if variant.get('colorName') == color:
                    inventory = variant.get('inventory', {})
                    return {
                        "total_available": inventory.get("quantityAvailable", 0),
                        "warehouses": inventory.get("warehouseQuantities", {}),
                        "incoming": inventory.get("incomingQuantity", 0),
                        "eta": inventory.get("eta"),
                        "min_quantity": inventory.get("minimumQuantity", 1),
                        "max_quantity": inventory.get("maximumQuantity"),
                        "last_updated": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking inventory: {str(e)}")
            return None

    def check_availability(self, style: str, color: str, min_qty: int = 24) -> Optional[Dict]:
        """Comprehensive check of product availability including price and inventory"""
        try:
            # Convert G640 to 64000 if needed
            if style.upper() == 'G640':
                style = '64000'
            
            params = {
                "style": f"Gildan {style}",
                "fields": "colorName,customerPrice,inventory,title,brand"
            }
            
            response = self._make_request(params)
            if not response:
                return None

            # Find matching color variant
            for variant in response:
                if variant.get('colorName') == color:
                    inventory = variant.get('inventory', {})
                    size_qty = {}
                    required_sizes = {'S', 'M', 'L', 'XL', '2XL'}
                    
                    for size in required_sizes:
                        size_qty[size] = inventory.get("warehouseQuantities", {}).get(size, 0)
                    
                    available = all(qty >= min_qty for qty in size_qty.values())
                    
                    return {
                        'available': available,
                        'price': variant.get('customerPrice'),
                        'bulk_pricing': variant.get('pricingGroups', []),
                        'inventory': size_qty,
                        'product_name': variant.get('title'),
                        'brand': variant.get('brand', {}).get('name')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in availability check: {str(e)}")
            logger.exception(e)
            return None