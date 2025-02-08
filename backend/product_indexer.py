from typing import Dict, List
import json
import os
from datetime import datetime
import logging
from collections import defaultdict

class ProductIndexer:
    """Indexes and maintains a searchable database of SanMar products with real-time inventory checking"""
    
    def __init__(self, sanmar_client):
        self.sanmar = sanmar_client
        self.product_db_path = 'data/product_database.json'
        self.last_updated = None
        self.products = {}
        self.attribute_index = defaultdict(list)
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        self.load_database()
    
    def load_database(self):
        """Load existing product database if it exists"""
        try:
            if os.path.exists(self.product_db_path):
                with open(self.product_db_path, 'r') as f:
                    data = json.load(f)
                    self.products = data['products']
                    self.last_updated = data['last_updated']
                    self.rebuild_attribute_index()
                    logging.info(f"Loaded {len(self.products)} products from database")
        except Exception as e:
            logging.error(f"Error loading product database: {str(e)}")
            self.products = {}
            self.last_updated = None
    
    def save_database(self):
        """Save current product database to disk"""
        try:
            with open(self.product_db_path, 'w') as f:
                json.dump({
                    'products': self.products,
                    'last_updated': datetime.now().isoformat()
                }, f)
            logging.info(f"Saved {len(self.products)} products to database")
        except Exception as e:
            logging.error(f"Error saving product database: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Common product attributes and their synonyms
        attribute_mapping = {
            'soft': ['soft', 'comfortable', 'plush', 'cozy'],
            'lightweight': ['light', 'lightweight', 'thin', 'airy'],
            'heavyweight': ['heavy', 'heavyweight', 'thick', 'substantial'],
            'athletic': ['athletic', 'sport', 'performance', 'moisture-wicking'],
            'basic': ['basic', 'essential', 'standard', 'classic'],
            'premium': ['premium', 'luxury', 'high-end', 'quality'],
            'affordable': ['affordable', 'budget', 'economical', 'value']
        }
        
        keywords = set()
        text = text.lower()
        
        # Extract direct matches and synonyms
        for category, terms in attribute_mapping.items():
            if any(term in text for term in terms):
                keywords.add(category)
        
        return list(keywords)
    
    def rebuild_attribute_index(self):
        """Build searchable index of product attributes"""
        self.attribute_index = defaultdict(list)
        
        for style, product in self.products.items():
            # Index product description words
            keywords = self._extract_keywords(product['description'])
            for keyword in keywords:
                self.attribute_index[keyword].append(style)
            
            # Index product categories
            category = product.get('category', '').lower()
            self.attribute_index[category].append(style)
            
            # Index brand
            brand = product.get('brand', '').lower()
            self.attribute_index[brand].append(style)
            
            # Index materials
            materials = self._parse_materials(product['description'])
            for material in materials:
                self.attribute_index[material].append(style)
    
    def _parse_materials(self, description: str) -> List[str]:
        """Extract material information from product description"""
        materials = []
        description = description.lower()
        
        material_indicators = {
            'cotton': ['cotton', '100% cotton', 'cotton blend'],
            'polyester': ['polyester', 'poly', '100% polyester'],
            'blend': ['blend', 'cotton/poly', 'poly/cotton'],
            'spandex': ['spandex', 'elastane'],
            'rayon': ['rayon', 'viscose'],
            'jersey': ['jersey'],
            'fleece': ['fleece'],
            'pique': ['pique']
        }
        
        for material, indicators in material_indicators.items():
            if any(indicator in description for indicator in indicators):
                materials.append(material)
        
        return materials
    
    def check_real_time_inventory(self, style: str, results: List[Dict]) -> List[Dict]:
        """Add real-time inventory data to product results"""
        try:
            # Get color/size combinations from product data
            colors = results[0].get('available_colors', ['White'])  # Default to white if no colors specified
            sizes = results[0].get('available_sizes', ['L'])      # Default to L if no sizes specified
            
            # Check inventory for each combination
            inventory_data = []
            for color in colors[:3]:  # Limit to 3 colors to avoid too many API calls
                for size in sizes[:3]:  # Limit to 3 sizes
                    try:
                        inventory = self.sanmar.check_inventory(style, color, size)
                        if inventory and inventory.get('total_available', 0) > 0:
                            inventory_data.append({
                                'color': color,
                                'size': size,
                                'available': inventory.get('total_available', 0),
                                'warehouses': inventory.get('warehouses', {})
                            })
                    except Exception as e:
                        logging.error(f"Error checking inventory for {style} {color} {size}: {str(e)}")
                        continue
            
            # Add inventory data to results
            for result in results:
                result['inventory'] = inventory_data
            
            return results
        except Exception as e:
            logging.error(f"Error checking real-time inventory: {str(e)}")
            return results
    
    def search(self, query: str, check_inventory: bool = True) -> List[Dict]:
        """Search products based on natural language query"""
        query_terms = query.lower().split()
        matching_styles = set()
        
        # Find products matching any query terms
        for term in query_terms:
            matching_styles.update(self.attribute_index.get(term, []))
            
            # Check for attribute matches
            keywords = self._extract_keywords(term)
            for keyword in keywords:
                matching_styles.update(self.attribute_index.get(keyword, []))
        
        # Convert styles to full product data
        results = []
        for style in matching_styles:
            if style in self.products:
                product = self.products[style].copy()
                
                # Get real-time price data
                try:
                    pricing = self.sanmar.get_pricing(style, None, None)
                    product['pricing'] = pricing
                except Exception as e:
                    logging.error(f"Error getting pricing for {style}: {str(e)}")
                    product['pricing'] = {}
                
                results.append(product)
        
        # Add real-time inventory data if requested
        if check_inventory and results:
            results = self.check_real_time_inventory(results[0]['style'], results)
        
        # Sort results by availability and relevance
        results.sort(key=lambda x: (
            bool(x.get('inventory', [])),  # Products with inventory first
            -len(x.get('inventory', [])),  # More available colors/sizes second
            float(x.get('pricing', {}).get('piece_price', 9999))  # Lower price third
        ))
        
        return results[:10]  # Limit to top 10 results