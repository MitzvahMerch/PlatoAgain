from zeep import Client, Settings
import logging
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv

class SanMarClient:
    """Client for interacting with SanMar's SOAP API services"""
    
    def __init__(self, username: str, password: str, customer_number: str):
        """Initialize the SanMar client with credentials
        
        Args:
            username: SanMar.com username
            password: SanMar.com password 
            customer_number: SanMar customer number
        """
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
            self.clients[service] = Client(url, settings=settings)
            
    def get_product_info(self, style: str, color: Optional[str] = None, size: Optional[str] = None) -> Dict:
        """Get product information for a specific style/color/size combination"""
        try:
            service = self.clients['product']
            
            # Build request parameters
            request_data = {
                'arg0': {
                    'style': style,
                    'color': color,
                    'size': size
                },
                'arg1': {
                    'sanMarCustomerNumber': self.customer_number,
                    'sanMarUserName': self.username,
                    'sanMarUserPassword': self.password
                }
            }
            
            # Make API call
            response = service.service.getProductInfoByStyleColorSize(**request_data)
            
            if response.errorOccurred:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_product_response(response.listResponse)
            
        except Exception as e:
            logging.error(f"Error getting product info: {str(e)}")
            raise

    def check_inventory(self, style: str, color: str, size: str) -> Dict:
        """Check inventory levels for a specific product"""
        try:
            service = self.clients['inventory']
            
            request_data = {
                'arg0': self.customer_number,
                'arg1': self.username,
                'arg2': self.password,
                'arg3': style,
                'arg4': color,
                'arg5': size
            }
            
            response = service.service.getInventoryQtyForStyleColorSize(**request_data)
            
            if response.errorOccurred:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_inventory_response(response.listResponse)
            
        except Exception as e:
            logging.error(f"Error checking inventory: {str(e)}")
            raise

    def get_pricing(self, style: str, color: str, size: str) -> Dict:
        """Get pricing information for a specific product"""
        try:
            service = self.clients['pricing']
            
            request_data = {
                'arg0': {
                    'style': style,
                    'color': color, 
                    'size': size
                },
                'arg1': {
                    'sanMarCustomerNumber': self.customer_number,
                    'sanMarUserName': self.username,
                    'sanMarUserPassword': self.password
                }
            }
            
            response = service.service.getPricing(**request_data)
            
            if response.errorOccurred:
                raise Exception(f"API Error: {response.message}")
                
            return self._process_pricing_response(response.listResponse)
            
        except Exception as e:
            logging.error(f"Error getting pricing: {str(e)}")
            raise

    def _process_product_response(self, response) -> Dict:
        """Process product response into a standardized format"""
        if not response:
            return {}
            
        product_info = {
            'style': getattr(response.productBasicInfo, 'style', ''),
            'title': getattr(response.productBasicInfo, 'productTitle', ''),
            'description': getattr(response.productBasicInfo, 'productDescription', ''),
            'brand': getattr(response.productBasicInfo, 'brandName', ''),
            'status': getattr(response.productBasicInfo, 'productStatus', ''),
            'available_sizes': getattr(response.productBasicInfo, 'availableSizes', ''),
            'images': {
                'front': getattr(response.productImageInfo, 'frontModel', ''),
                'back': getattr(response.productImageInfo, 'backModel', ''),
                'thumbnail': getattr(response.productImageInfo, 'thumbnailImage', '')
            }
        }
        return product_info

    def _process_inventory_response(self, response) -> Dict:
        """Process inventory response into a standardized format"""
        if not response:
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
        
        # Response contains array of quantities by warehouse
        for i, qty in enumerate(response):
            whse_num = str(i + 1)
            if whse_num in warehouses:
                inventory['warehouses'][warehouses[whse_num]] = qty
                inventory['total_available'] += qty
                
        return inventory

    def _process_pricing_response(self, response) -> Dict:
        """Process pricing response into a standardized format"""
        if not response:
            return {}
            
        return {
            'piece_price': getattr(response, 'piecePrice', 0),
            'case_price': getattr(response, 'casePrice', 0),
            'sale_price': getattr(response, 'pieceSalePrice', 0),
            'price_text': getattr(response, 'priceText', ''),
            'sale_start_date': getattr(response, 'saleStartDate', None),
            'sale_end_date': getattr(response, 'saleEndDate', None)
        }