import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class SSClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.ssactivewear.com/v2"
        
        # Setup session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None) -> Dict:
        """Make request to S&S API with error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"
            logger.debug(f"Making {method} request to {url} with params: {params}")
            
            response = self.session.request(method, url, params=params, timeout=10)
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API error: Status {response.status_code}, Response: {response.text}")
                return None
                
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for endpoint: {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            logger.exception(e)
            return None

    def get_product_info(self, style: str) -> Optional[Dict]:
        """Get basic product information by style number"""
        try:
            response = self._make_request(f"products/{style}")
            if not response:
                logger.warning(f"No product info found for style {style}")
                return None
                
            # Extract relevant product information
            product_info = {
                "style": style,
                "title": response.get("title"),
                "description": response.get("description"),
                "brand": response.get("brand", {}).get("name"),
                "colors": [color.get("name") for color in response.get("colors", [])],
                "sizes": [size.get("label") for size in response.get("sizes", [])],
                "msrp": response.get("msrp"),
                "category": response.get("category", {}).get("name")
            }
            return product_info
        except Exception as e:
            logger.error(f"Error getting product info for style {style}: {str(e)}")
            return None

    def get_pricing(self, style: str, color: str = None, size: str = None) -> Optional[Dict]:
        """Get pricing information for a product"""
        try:
            params = {"style": style}
            if color:
                params["color"] = color
            if size:
                params["size"] = size
                
            response = self._make_request("pricing", params=params)
            if not response:
                return None

            # Extract pricing information with bulk discounts
            pricing = {
                "piece_price": response.get("piecePrice"),
                "case_price": response.get("casePrice"),
                "case_quantity": response.get("caseQuantity"),
                "pricing_groups": response.get("pricingGroups", []),
                "min_quantity": response.get("minimumQuantity", 1),
                "bulk_discounts": self._extract_bulk_discounts(response)
            }
            return pricing
        except Exception as e:
            logger.error(f"Error getting pricing for style {style}: {str(e)}")
            return None

    def _extract_bulk_discounts(self, pricing_data: Dict) -> List[Dict]:
        """Extract bulk discount tiers from pricing data"""
        discounts = []
        for tier in pricing_data.get("pricingGroups", []):
            discounts.append({
                "quantity": tier.get("minimumQuantity"),
                "price": tier.get("price"),
                "discount_percentage": tier.get("discountPercentage")
            })
        return sorted(discounts, key=lambda x: x["quantity"])

    def check_inventory(self, style: str, color: str = None, size: str = None) -> Optional[Dict]:
        """Check inventory levels for a specific product variant"""
        try:
            params = {
                "style": style
            }
            if color:
                params["color"] = color
            if size:
                params["size"] = size
            
            response = self._make_request("inventory", params=params)
            if not response:
                return None

            # Extract inventory information with warehouse details
            inventory = {
                "total_available": response.get("quantityAvailable", 0),
                "warehouses": response.get("warehouseQuantities", {}),
                "incoming": response.get("incomingQuantity", 0),
                "eta": response.get("eta"),
                "min_quantity": response.get("minimumQuantity", 1),
                "max_quantity": response.get("maximumQuantity"),
                "last_updated": datetime.now().isoformat()
            }
            return inventory
        except Exception as e:
            logger.error(f"Error checking inventory for style {style}: {str(e)}")
            return None

    def search_products(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search products using keywords and optional filters"""
        try:
            params = {"q": query}
            if filters:
                params.update(filters)
                
            response = self._make_request("products/search", params=params)
            
            products = []
            for item in response.get("items", []):
                product = {
                    "style": item.get("styleNumber"),
                    "title": item.get("title"),
                    "brand": item.get("brand", {}).get("name"),
                    "thumbnail": item.get("thumbnailUrl"),
                    "colors": [color.get("name") for color in item.get("colors", [])],
                    "msrp": item.get("msrp"),
                    "category": item.get("category", {}).get("name"),
                    "available": item.get("isAvailable", False)
                }
                products.append(product)
            
            return products
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    def get_product_specs(self, style: str) -> Optional[Dict]:
        """Get detailed product specifications"""
        try:
            response = self._make_request(f"products/{style}/specifications")
            if not response:
                return None
                
            return {
                "material": response.get("material"),
                "weight": response.get("weight"),
                "features": response.get("features", []),
                "specifications": response.get("specifications", {}),
                "care_instructions": response.get("careInstructions", []),
                "size_chart": response.get("sizeChart"),
                "certifications": response.get("certifications", [])
            }
        except Exception as e:
            logger.error(f"Error getting product specs for style {style}: {str(e)}")
            return None

    def check_availability(self, style: str, color: str, min_qty: int = 24) -> Optional[Dict]:
        """Comprehensive check of product availability including price and inventory"""
        try:
            # Get base product info
            product_info = self.get_product_info(style)
            if not product_info:
                return None

            # Get pricing
            pricing = self.get_pricing(style, color)
            if not pricing:
                return None

            # Check inventory
            inventory = self.check_inventory(style, color)
            if not inventory:
                return None

            # Check if we have sufficient quantity across required sizes
            required_sizes = {'S', 'M', 'L', 'XL', '2XL'}
            size_qty = {
                size: inventory.get("warehouses", {}).get(size, 0)
                for size in required_sizes
            }
            
            available = all(
                qty >= min_qty for qty in size_qty.values()
            )

            return {
                'available': available,
                'price': pricing.get('piece_price'),
                'bulk_pricing': pricing.get('bulk_discounts'),
                'inventory': size_qty,
                'product_name': product_info.get('title'),
                'brand': product_info.get('brand'),
                'material': product_info.get('specifications', {}).get('material')
            }

        except Exception as e:
            logger.error(f"Error in comprehensive availability check: {str(e)}")
            logger.exception(e)
            return None