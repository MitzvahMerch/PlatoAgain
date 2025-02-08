from zeep import Client, Settings
import logging
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv

class SanMarClient:
    """Client for interacting with SanMar's SOAP API services"""
    
    def __init__(self, username: str, password: str, customer_number: str):
        """Initialize the SanMar client with credentials"""
        self.username = username
        self.password = password
        self.customer_number = customer_number
        
        # Base URLs for different services
        self.base_urls = {
            'product': 'https://ws.sanmar.com:8080/SanMarWebService/SanMarProductInfoServicePort?wsdl',
            'inventory': 'https://ws.sanmar.com:8080/SanMarWebService/SanMarWebServicePort?wsdl',
            'pricing': 'https://ws.sanmar.com:8080/SanMarWebService/SanMarPricingServicePort?wsdl'
        }
        
        # Initialize service clients
        self.clients = {}
        settings = Settings(strict=False, xml_huge_tree=True)
        
        for service, url in self.base_urls.items():
            try:
                self.clients[service] = Client(url, settings=settings)
                logging.info(f"Successfully initialized {service} client")
            except Exception as e:
                logging.error(f"Error initializing {service} client: {str(e)}")
                raise
            
    def get_product_info(self, style: str, color: Optional[str] = None, size: Optional[str] = None) -> Dict:
        """Get product information for a specific style/color/size combination"""
        try:
            service = self.clients['product']
            
            # Create product search object
            product = {
                'style': style,
                'color': color if color else '',
                'size': size if size else ''
            }
            
            # Create user object
            user = {
                'sanMarCustomerNumber': self.customer_number,
                'sanMarUserName': self.username,
                'sanMarUserPassword': self.password
            }
            
            logging.info(f"Making product info request for style {style}")
            
            # Call using the correct method name
            response = service.service.getProductInfoByStyleColorSize(
                arg0=product,
                arg1=user
            )
            
            # Log raw response for debugging
            logging.debug(f"Raw product info response: {response}")
            
            # Check for error response
            if hasattr(response, 'message') and response.message and 'ERROR' in response.message:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_product_response(response)
            
        except Exception as e:
            logging.error(f"Error getting product info: {str(e)}")
            raise

    def check_inventory(self, style: str, color: str, size: str) -> Dict:
        """Check inventory levels for a specific product"""
        try:
            service = self.clients['inventory']
            
            logging.info(f"Checking inventory for {style} {color} {size}")
            
            # Pass arguments in the correct order according to the signature
            response = service.service.getInventoryQtyForStyleColorSize(
                arg0=self.customer_number,
                arg1=self.username,
                arg2=self.password,
                arg3=style,
                arg4=color,
                arg5=size
            )
            
            # Log raw response for debugging
            logging.debug(f"Raw inventory response: {response}")
            
            # Check for error response
            if hasattr(response, 'message') and response.message and 'ERROR' in response.message:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_inventory_response(response)
            
        except Exception as e:
            logging.error(f"Error checking inventory: {str(e)}")
            raise

    def get_pricing(self, style: str, color: str, size: str) -> Dict:
        """Get pricing information for a specific product"""
        try:
            service = self.clients['pricing']
            
            # Create item array with a single item
            items = [{
                'style': style,
                'color': color,
                'size': size
            }]
            
            # Create user object according to the expected type
            user = {
                'sanMarCustomerNumber': self.customer_number,
                'sanMarUserName': self.username,
                'sanMarUserPassword': self.password
            }
            
            logging.info(f"Getting pricing for {style} {color} {size}")
            
            # Call using the correct parameter structure
            response = service.service.getPricing(
                arg0=items,
                arg1=user
            )
            
            # Log raw response for debugging
            logging.debug(f"Raw pricing response: {response}")
            
            # Check for error response
            if hasattr(response, 'message') and response.message and 'ERROR' in response.message:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_pricing_response(response)
            
        except Exception as e:
            logging.error(f"Error getting pricing: {str(e)}")
            raise

    def _process_product_response(self, response) -> Dict:
        """Process product response into a standardized format"""
        if not response:
            return {}
            
        # Extract basic product info
        info = getattr(response, 'listResponse', [])
        if not info or not len(info):
            return {}
            
        product_info = info[0]
        basic_info = getattr(product_info, 'productBasicInfo', None)
        
        if not basic_info:
            return {}
            
        result = {
            'style': getattr(basic_info, 'style', ''),
            'title': getattr(basic_info, 'productTitle', ''),
            'description': getattr(basic_info, 'productDescription', ''),
            'brand': getattr(basic_info, 'brandName', ''),
            'status': getattr(basic_info, 'productStatus', ''),
            'available_sizes': getattr(basic_info, 'availableSizes', []),
            'images': {}
        }
        
        # Extract image info if available
        image_info = getattr(product_info, 'productImageInfo', None)
        if image_info:
            result['images'] = {
                'front': getattr(image_info, 'frontModel', ''),
                'back': getattr(image_info, 'backModel', ''),
                'thumbnail': getattr(image_info, 'thumbnailImage', '')
            }
            
        return result

    def _process_inventory_response(self, response) -> Dict:
        """Process inventory response into a standardized format"""
        if not response or not hasattr(response, 'listResponse'):
            return {}
            
        warehouses = {
            '1': 'Seattle, WA',
            '2': 'Cincinnati, OH',
            '3': 'Dallas, TX',
            '4': 'Reno, NV',
            '5': 'Robbinsville, NJ',
            '6': 'Jacksonville, FL',
            '7': 'Minneapolis, MN',
            '12': 'Phoenix, AZ',
            '31': 'Richmond, VA'
        }
        
        inventory = {
            'total_available': 0,
            'warehouses': {}
        }
        
        quantities = response.listResponse
        if not isinstance(quantities, list):
            quantities = [quantities]
            
        for i, qty in enumerate(quantities):
            whse_num = str(i + 1)
            if whse_num in warehouses:
                inv_qty = int(qty) if qty is not None else 0
                inventory['warehouses'][warehouses[whse_num]] = inv_qty
                inventory['total_available'] += inv_qty
                
        return inventory

    def _process_pricing_response(self, response) -> Dict:
        """Process pricing response into a standardized format"""
        if not response or not hasattr(response, 'listResponse'):
            return {}
            
        pricing_info = response.listResponse[0] if response.listResponse else None
        if not pricing_info:
            return {}
            
        return {
            'piece_price': getattr(pricing_info, 'piecePrice', 0),
            'case_price': getattr(pricing_info, 'casePrice', 0),
            'sale_price': getattr(pricing_info, 'pieceSalePrice', 0),
            'price_text': getattr(pricing_info, 'priceText', ''),
            'sale_start_date': getattr(pricing_info, 'saleStartDate', None),
            'sale_end_date': getattr(pricing_info, 'saleEndDate', None)
        }