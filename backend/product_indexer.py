from typing import Dict, List
import json
import os
from datetime import datetime
import logging
from collections import defaultdict
import pandas as pd

class ProductIndexer:
    """Intelligent product search and recommendation engine for SanMar products"""
    
    def __init__(self, sanmar_client):
        self.sanmar = sanmar_client
        self.product_db_path = 'data/product_database.json'
        self.last_updated = None
        self.products = {}
        self.attribute_index = defaultdict(list)
        
        # Common category mappings
        self.product_categories = {
            't-shirt': ['t-shirt', 'tee', 'tshirt', 'shirt'],
            'polo': ['polo', 'golf shirt'],
            'hoodie': ['hoodie', 'hooded', 'sweatshirt'],
            'jacket': ['jacket', 'coat'],
            'tank': ['tank', 'sleeveless'],
            'long sleeve': ['long sleeve', 'longsleeve']
        }
        
        # Material property mappings
        self.material_properties = {
            'soft': ['soft', 'comfortable', 'plush', 'cozy', 'ring-spun'],
            'lightweight': ['light', 'lightweight', 'thin'],
            'heavyweight': ['heavy', 'heavyweight', 'thick'],
            'breathable': ['breathable', 'airy', 'moisture-wicking'],
            'durable': ['durable', 'strong', 'lasting']
        }
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
        # Load or build product database
        self.load_database()
        if not self.products or self._database_needs_update():
            self.build_product_database()

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

    def build_product_database(self):
        """Build product database from SanMar FTP data files"""
        try:
            # Load SDL_N file for basic product info
            sdl_path = 'data/SanMar_SDL_N.csv'
            if not os.path.exists(sdl_path):
                logging.error("SanMar_SDL_N.csv not found")
                return
                
            df_sdl = pd.read_csv(sdl_path)
            
            # Load EPDD file for additional info
            epdd_path = 'data/SanMar_EPDD.csv'
            if os.path.exists(epdd_path):
                df_epdd = pd.read_csv(epdd_path)
                # Merge relevant columns from EPDD
                df = pd.merge(df_sdl, df_epdd[['UNIQUE_KEY', 'QTY']], on='UNIQUE_KEY', how='left')
            else:
                df = df_sdl
            
            # Convert to dictionary format
            self.products = {}
            for _, row in df.iterrows():
                unique_key = str(row['UNIQUE_KEY'])
                self.products[unique_key] = {
                    'style': row['STYLE#'],
                    'title': row['PRODUCT_TITLE'],
                    'description': row['PRODUCT_DESCRIPTION'],
                    'brand': row.get('MILL', ''),
                    'available_sizes': row['AVAILABLE_SIZES'],
                    'category': row.get('CATEGORY_NAME', ''),
                    'subcategory': row.get('SUBCATEGORY_NAME', ''),
                    'colors': [row['COLOR_NAME']] if 'COLOR_NAME' in row else [],
                    'weight': row.get('PIECE_WEIGHT', 0),
                    'inventory_key': row.get('INVENTORY_KEY', ''),
                    'size_index': row.get('SIZE_INDEX', ''),
                    'product_status': row.get('PRODUCT_STATUS', 'Active'),
                    'mainframe_color': row.get('SANMAR_MAINFRAME_COLOR', ''),
                    'msrp': row.get('MSRP', 0),
                    'bulk_inventory': row.get('QTY', 0)
                }

            self.last_updated = datetime.now().isoformat()
            self.save_database()
            self.rebuild_attribute_index()
            logging.info(f"Successfully built database with {len(self.products)} products")
            
        except Exception as e:
            logging.error(f"Error building product database: {str(e)}")

    def _database_needs_update(self) -> bool:
        """Check if database needs to be updated (older than 24 hours)"""
        if not self.last_updated:
            return True
            
        try:
            last_update = datetime.fromisoformat(self.last_updated)
            age = datetime.now() - last_update
            return age.days >= 1
        except:
            return True

    def save_database(self):
        """Save current product database to disk"""
        try:
            with open(self.product_db_path, 'w') as f:
                json.dump({
                    'products': self.products,
                    'last_updated': self.last_updated
                }, f)
            logging.info(f"Saved {len(self.products)} products to database")
        except Exception as e:
            logging.error(f"Error saving product database: {str(e)}")

    def rebuild_attribute_index(self):
        """Build searchable index of product attributes"""
        self.attribute_index = defaultdict(list)
        
        for unique_key, product in self.products.items():
            # Index all text fields
            for field in ['title', 'description', 'brand', 'category', 'subcategory']:
                text = product.get(field, '').lower()
                words = text.split()
                for word in words:
                    self.attribute_index[word].append(unique_key)
            
            # Index colors
            for color in product.get('colors', []):
                self.attribute_index[color.lower()].append(unique_key)
                
            # Index category terms
            for category, terms in self.product_categories.items():
                if any(term in product['description'].lower() for term in terms):
                    self.attribute_index[category].append(unique_key)
                    
            # Index material properties
            for prop, terms in self.material_properties.items():
                if any(term in product['description'].lower() for term in terms):
                    self.attribute_index[prop].append(unique_key)

    def _extract_requirements(self, query: str) -> Dict:
        """Extract product requirements from natural language query"""
        query = query.lower()
        requirements = {
            'category': None,
            'properties': [],
            'colors': [],
            'brand': None,
            'size_range': None
        }
        
        # Extract category
        for category, terms in self.product_categories.items():
            if any(term in query for term in terms):
                requirements['category'] = category
                break
        
        # Extract material properties
        for prop, terms in self.material_properties.items():
            if any(term in query for term in terms):
                requirements['properties'].append(prop)
        
        # Extract brand (you can expand this list)
        brands = ['gildan', 'port & company', 'sport-tek', 'nike']
        for brand in brands:
            if brand in query:
                requirements['brand'] = brand
                break
        
        # Extract size range
        if 'youth' in query or 'kids' in query:
            requirements['size_range'] = 'youth'
        elif 'adult' in query:
            requirements['size_range'] = 'adult'
            
        return requirements

    def search(self, query: str, check_inventory: bool = True) -> List[Dict]:
        """Search products based on natural language query"""
        requirements = self._extract_requirements(query)
        logging.info(f"Extracted requirements: {requirements}")
        
        # Find matching products
        matching_products = []
        seen_styles = set()
        
        # First try to match all requirements
        for unique_key, product in self.products.items():
            if product['style'] in seen_styles:
                continue
                
            score = 0
            
            # Category match
            if requirements['category']:
                if any(term in product['description'].lower() for term in self.product_categories[requirements['category']]):
                    score += 3
                    
            # Property matches
            for prop in requirements['properties']:
                if any(term in product['description'].lower() for term in self.material_properties[prop]):
                    score += 1
                    
            # Brand match
            if requirements['brand'] and requirements['brand'].lower() in product['brand'].lower():
                score += 2
                
            # Size range match
            if requirements['size_range']:
                if requirements['size_range'] in product['available_sizes'].lower():
                    score += 1
                    
            if score > 0:
                # Get real-time inventory if requested
                if check_inventory:
                    try:
                        inventory = self.sanmar.check_inventory(
                            product['style'],
                            product['mainframe_color'],
                            'M'  # Check medium size as sample
                        )
                        product['current_inventory'] = inventory
                    except Exception as e:
                        logging.error(f"Error checking inventory: {str(e)}")
                        product['current_inventory'] = None
                
                matching_products.append((score, product))
                seen_styles.add(product['style'])
        
        # Sort by score
        matching_products.sort(key=lambda x: x[0], reverse=True)
        
        # Return top matches
        return [p for _, p in matching_products[:10]]

    def process_product_response(self, response: Dict) -> Dict:
        """Process a raw product response into a standardized format"""
        # ... (keep existing method as is)
        pass