import os
import base64
import requests
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    def get_price(self, style: str, color: str) -> Optional[float]:
        """Get price for a specific style and color"""
        try:
            # For Softstyle G640, use 64000
            if style.upper() == 'G640':
                style_param = "Gildan 64000"
            else:
                style_param = f"Gildan {style}"
            
            # Use exact endpoint format from working curl
            url = f"{self.base_url}/products/"
            params = {
                "style": style_param,
                "fields": "colorName,customerPrice"
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data:  # If we got data, look for the color
                    for variant in data:
                        if variant.get('colorName') == color:
                            return variant.get('customerPrice')
                    
            return None
            
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None