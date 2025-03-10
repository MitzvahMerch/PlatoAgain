import logging
from typing import Dict, List, Optional, Tuple
import os
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class ProductCategory:
    """Represents a category of products with similar attributes"""
    
    def __init__(self, name: str, products: List[Dict] = None, claude_client=None):
        self.name = name
        self.products = products or []
        self.claude_client = claude_client
        
    def add_product(self, product: Dict):
        """Add a product to this category"""
        self.products.append(product)


class ProductDecisionTree:
    """Decision tree for product selection"""
    
    def __init__(self, claude_client=None):
        self.categories = {}
        self.product_data = {}
        self.claude_client = claude_client
        self.init_product_data()
    
    def parse_sonar_analysis(self, analysis_text: str) -> Dict:
        """Parse the structured output from Claude's analysis"""
        preferences = {}
        
        # Define patterns to extract each preference
        patterns = {
            'category': r'Category:\s*([^\n]+)',
            'color': r'Color:\s*([^\n]+)',
            'material': r'Material:\s*([^\n]+)',
            'brand': r'Brand:\s*([^\n]+)',
            'price': r'Price Point:\s*([^\n]+)',
            'fit': r'Fit:\s*([^\n]+)',
            'size': r'Size:\s*([^\n]+)'
        }
        
        # Extract each preference
        for key, pattern in patterns.items():
            match = re.search(pattern, analysis_text)
            if match:
                value = match.group(1).strip()
                # Only include preferences that aren't "None"
                if value.lower() != "none":
                    preferences[key] = value
        
        logger.info(f"Parsed preferences (excluding None values): {preferences}")
        return preferences
    
    def map_category_to_internal(self, category: str) -> str:
        """Map Claude's category to our internal category names"""
        category = category.lower()
        
        category_map = {
            't-shirt': 't-shirt',
            'sweatshirt': 'hoodie',  # Map Sweatshirt to hoodie category
            'long sleeve shirt': 'long-sleeve',
            'crewneck': 'crewneck',
            'sweatpants': 'sweatpants'
        }
        
        # Find the matching category
        for key, value in category_map.items():
            if key in category:
                return value
        
        # Default to t-shirt if no match
        logger.warning(f"Could not map category '{category}' to internal category, defaulting to t-shirt")
        return 't-shirt'
    
    def select_product_with_claude(self, category: str, user_query: str, preferences: Dict) -> Tuple[Optional[Dict], str]:
        """Use Claude to select the best product from a category based on preferences"""
        
        # Get all products in the category
        if category not in self.categories:
            logger.warning(f"Category {category} not found, defaulting to t-shirt")
            category = 't-shirt'
            
        products = self.categories[category].products
        
        # Create a formatted list of products with key attributes
        product_options = []
        for product in products:
            # Extract material type category
            material_type = "100% Cotton" if "100% cotton" in product['material'].lower() else \
                           "Athletic/Polyester" if "polyester" in product['material'].lower() else \
                           "Cotton/Poly Blend"
            
            product_options.append(
                f"Product: {product['product_name']}\n"
                f"Color: {product['color']}\n"
                f"Material: {product['material']} (Type: {material_type})\n"
                f"Brand: {product['product_name'].split(' ')[0]}\n"  # Extract brand from name
                f"Price: {product['price']}\n"
            )
        
        product_list = "\n---\n".join(product_options)
        
        # Build the priorities section based on what was specified
        priorities = ["1. COLOR MATCH - This is the absolute most important factor"]
        
        if "material" in preferences:
            priorities.append("2. MATERIAL TYPE - Must match the specified material type")
            priorities.append("3. BRAND - If customer mentioned a specific brand")
            priorities.append("4. PRICE - Match budget/affordable to cheaper options, premium/quality to higher-end")
        elif "brand" in preferences:
            priorities.append("2. BRAND - Must match the specified brand")
            priorities.append("3. PRICE - Match budget/affordable to cheaper options, premium/quality to higher-end")
        else:
            priorities.append("2. PRICE - Match budget/affordable to cheaper options, premium/quality to higher-end")
        
        priorities_text = "\n".join(priorities)
        
        # List only the specified preferences
        preferences_text = "\n".join([f"{k.capitalize()}: {v}" for k, v in preferences.items()])
        
        # Create the prompt for Claude
        prompt = [
            {"role": "system", "content": f"""
            You are a product matching expert for a custom apparel print shop. 
            The customer has requested: "{user_query}"
            
            We've identified these preferences:
            {preferences_text}
            
            Available options in this category:
            {product_list}
            
            Select the BEST match based on these priorities:
            {priorities_text}
            
            CRITICAL RULES:
            - COLOR is always the #1 priority - find the closest color match
            - If MATERIAL was specified, it must be the second priority
            - If multiple products are equal on higher priorities, use lower priorities as tiebreakers
            - Never sacrifice a better color match for other attributes
            
            Explain your decision focusing on how it matches the customer's requirements.
            Then provide the exact product name and color as your final answer in this format:
            SELECTED: [Product Name] in [Color]
            """},
            {"role": "user", "content": "Select the best product match."}
        ]
        
        # Call Claude API
        try:
            response = self.claude_client.call_api(prompt, temperature=0.2)
            
            # Extract the selected product
            match = re.search(r"SELECTED: (.+) in (.+)$", response, re.MULTILINE)
            if match:
                product_name = match.group(1).strip()
                color = match.group(2).strip()

                # Log Claude's response and the extracted values
                logger.info(f"Claude's raw selection: SELECTED: {product_name} in {color}")
                logger.info(f"Claude's response excerpt: {response[-200:]}")

                for idx, product in enumerate(products[:5]):  # Log first 5 products for brevity
                    logger.info(f"Product {idx}: '{product['product_name']}' in '{product['color']}'")
                
                # Find the matching product
                for product in products:
                    # Improved normalization - remove punctuation, lowercase, and strip spaces
                    product_name_norm = re.sub(r'[^\w\s]', '', product['product_name']).lower().strip()
                    product_color_norm = re.sub(r'[^\w\s]', '', product['color']).lower().strip()
                    match_name_norm = re.sub(r'[^\w\s]', '', product_name).lower().strip()
                    match_color_norm = re.sub(r'[^\w\s]', '', color).lower().strip()
                    
                    # Exact match check with normalized strings
                    if product_name_norm == match_name_norm and product_color_norm == match_color_norm:
                        return product, response
                    
                    # Partial match check as fallback
                    elif match_name_norm in product_name_norm and match_color_norm in product_color_norm:
                        return product, response
                
                logger.warning(f"Could not find exact product match for '{product_name}' in '{color}'")
                
                # If no exact match found but color was specified, try to find product in the specified color
                if 'color' in preferences:
                    requested_color = preferences['color'].lower()
                    color_matches = []
                    
                    logger.info(f"Trying to find color match for: {requested_color}")
                    for product in products:
                        product_color = product['color'].lower()
                        if requested_color in product_color or any(word in product_color for word in requested_color.split()):
                            logger.info(f"Found color match: {product['product_name']} in {product['color']}")
                            color_matches.append(product)
                    
                    if color_matches:
                        # Return the first color match
                        logger.info(f"Fallback to color match: {color_matches[0]['product_name']} in {color_matches[0]['color']}")
                        return color_matches[0], "Fallback to color match: No exact product match found, but matched requested color."
            else:
                logger.warning(f"Could not parse product selection from Claude's response")
                
        except Exception as e:
            logger.error(f"Error in Claude product selection: {str(e)}")
            response = f"Error: {str(e)}"
        
        # Improved fallback logic - try to match any specified preferences
        if products:
            # Try to find a product matching the color first if specified
            if 'color' in preferences:
                requested_color = preferences['color'].lower()
                for product in products:
                    if requested_color in product['color'].lower():
                        logger.warning(f"Fallback to color match: {product['product_name']} in {product['color']}")
                        return product, "Fallback to color match"
            
            # Try to find a product matching the material if specified
            if 'material' in preferences:
                requested_material = preferences['material'].lower()
                for product in products:
                    if requested_material in product['material'].lower():
                        logger.warning(f"Fallback to material match: {product['product_name']} with {product['material']}")
                        return product, "Fallback to material match"
            
            # Last resort - return first product in category
            logger.warning(f"Fallback to first product in category: {products[0]['product_name']}")
            return products[0], "Fallback to first product in category"
        
        return None, response
    
    def select_product(self, query: str, sonar_analysis: str) -> Optional[Dict]:
        """
        Select a product based on user query and Claude's analysis.
        Returns product details dictionary with explanation.
        """
        try:
            # Parse the structured analysis from Claude
            preferences = self.parse_sonar_analysis(sonar_analysis)
            
            # Get the category from Claude's analysis
            original_category = None
            if 'category' in preferences:
                # Save the original category from Claude
                original_category = preferences['category']
                # Map the Claude category to our internal category
                category = self.map_category_to_internal(preferences['category'])
            else:
                category = 't-shirt'  # Default category
                original_category = "T-Shirt"  # Default category name
            
            logger.info(f"Category identified: {category}")
            logger.info(f"Original category from Claude: {original_category}")
            logger.info(f"Preferences extracted: {preferences}")
            
            # Use Claude to select the best product from this category
            selected_product, explanation = self.select_product_with_claude(category, query, preferences)
            
            if selected_product:
                logger.info(f"Selected product: {selected_product['product_name']} in {selected_product['color']}")
                # Add the explanation to the product info
                selected_product['match_explanation'] = explanation
                # Add the original category from Claude's analysis
                selected_product['category'] = original_category
                logger.info(f"Added category to product: {original_category}")
                return selected_product
            
            # Fallback to default product
            logger.warning("No product selected, falling back to default")
            default_product = None
            
            if 't-shirt' in self.categories and self.categories['t-shirt'].products:
                default_product = self.categories['t-shirt'].products[0].copy()  # Create a copy to avoid modifying the original
                default_product['category'] = original_category or "T-Shirt"  # Set the category
                logger.info(f"Set category on default product: {default_product['category']}")
                return default_product
            return None
                
        except Exception as e:
            logger.error(f"Error in product selection: {str(e)}")
            # Default product if there's an error
            if self.categories.get('t-shirt') and self.categories['t-shirt'].products:
                default_product = self.categories['t-shirt'].products[0].copy()  # Create a copy
                default_product['category'] = "T-Shirt"  # Add default category
                return default_product
            return None
    
    def get_product_by_style_color(self, style: str, color: str) -> Optional[Dict]:
        """Get product by style number and color"""
        key = f"{style}_{color}"
        return self.product_data.get(key)
    
    def init_product_data(self):
        """Initialize the product data with preset prices and details"""
        # T-Shirts category
        self.categories['t-shirt'] = ProductCategory('T-Shirts', claude_client=self.claude_client)
        
        # JERZEES - Dri-Power 50/50 T-Shirt
        jerzees_colors = [
            "White", "Black", "Aquatic_Blue", "Ash", "Athletic_Heather", "Black_Heather", 
            "Burnt_Orange", "California_Blue", "Cardinal", "Charcoal_Grey", "Classic_Pink", 
            "Columbia_Blue", "Cool_Mint", "Cyber_Pink", "Deep_Purple", "Forest_Green", 
            "Gold", "Irish_Green_Heather", "Island_Yellow", "J._Navy", "Jade", "Kelly", 
            "Kiwi", "Light_Blue", "Maroon", "Military_Green", "Neon_Green", "Neon_Pink", 
            "Neon_Yellow", "Oxford", "Royal", "Safety_Green", "Safety_Orange", "Scuba_Blue", 
            "Silver", "Tennessee_Orange", "True_Red", "Vintage_Heather_Blue", 
            "Vintage_Heather_Maroon", "Vintage_Heather_Navy", "Vintage_Heather_Red", "Violet"
        ]
        
        for color in jerzees_colors:
            self.categories['t-shirt'].add_product({
                'style_number': '29M',
                'product_name': 'JERZEES - Dri-Power 50/50 T-Shirt',
                'color': color.replace("_", " "),
                'price': '$12.36',
                'material': '50/50 cotton/polyester',
                'weight': 'midweight',
                'fit': 'regular',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'S-5XL',
                'features': [
                    'Advanced moisture-management performance',
                    'Noticeably softer hand & excellent printability',
                    'Shoulder-to-shoulder taping',
                    'Tear away label'
                ],
                'images': {
                    'front': f'/productimages/29MR/JERZEES_29MR_{color}_Front_High.jpg',
                    'back': f'/productimages/29MR/JERZEES_29MR_{color}_Back_High.jpg'
                }
            })
            
        # Sport-Tek PosiCharge Competitor Tee
        sporttek_colors = [
            {"display": "Atomic Blue", "filename": "ST350_Atomic Blue_Flat"},
            {"display": "Black", "filename": "ST350_Black_flat"},
            {"display": "Cardinal", "filename": "ST350_cardinal_flat"},
            {"display": "Carolina Blue", "filename": "ST350_Carolina Blue_Flat"},
            {"display": "Deep Orange", "filename": "ST350_Deep Orange_Flat"},
            {"display": "Deep Red", "filename": "ST350_DEEP RED_Flat"},
            {"display": "Forest Green", "filename": "ST350_Forest Green_Flat"},
            {"display": "Gold", "filename": "ST350_gold_flat"},
            {"display": "Grey Concrete", "filename": "ST350_Grey Concrete_Flat"},
            {"display": "Grey Concrete Heather", "filename": "ST350_Grey Concrete Heather_Flat"},
            {"display": "Iron Grey", "filename": "ST350_Iron Grey_Flat"},
            {"display": "Iron Grey Heather", "filename": "ST350_Iron Grey Heather_Flat"},
            {"display": "Kelly Green", "filename": "ST350_Kelly Green_Flat"},
            {"display": "Lime Shock", "filename": "ST350_Lime Shock_Flat"},
            {"display": "Maroon", "filename": "ST350_maroon_flat"},
            {"display": "Neon Orange", "filename": "ST350_Neon Orange_Flat"},
            {"display": "Neon Pink", "filename": "ST350_Neon Pink_Flat"},
            {"display": "Neon Yellow", "filename": "ST350_Neon Yellow_Flat"},
            {"display": "Purple", "filename": "ST350_purple_flat"},
            {"display": "Royal", "filename": "ST350_Royal_Flat"},
            {"display": "Silver", "filename": "ST350_silver_flat"},
            {"display": "Texas Orange", "filename": "ST350_Texas Orange_Flat"},
            {"display": "Tropic Blue", "filename": "ST350_Tropic Blue_Flat"},
            {"display": "True Navy", "filename": "ST350_True Navy_Flat"},
            {"display": "True Red", "filename": "ST350_True Red_Flat"},
            {"display": "True Royal Heather", "filename": "ST350_True Royal Heather_Flat"},
            {"display": "White", "filename": "ST350_white_flat"}
        ]
        
        for color in sporttek_colors:
            self.categories['t-shirt'].add_product({
                'style_number': 'ST350',
                'product_name': 'Sport-Tek PosiCharge Competitor Tee',
                'color': color["display"],
                'price': '$13.99',
                'material': '100% polyester',
                'weight': 'lightweight',
                'fit': 'athletic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'XS-4XL',
                'features': [
                    'Moisture-wicking',
                    'PosiCharge technology to lock in color',
                    'Removable tag for comfort and relabeling'
                ],
                'images': {
                    'front': f'/productimages/ST350/{color["filename"]}_Front.jpg',
                    'back': f'/productimages/ST350/{color["filename"]}_Back.jpg'
                }
            })
            
        # Bella + Canvas Jersey Tee
        bella_colors = [
            "White", "Black", "Ash", "Asphalt", "Berry", "Blue_Storm", "Cardinal", 
            "Columbia_Blue", "Dark_Grey", "Dusty_Blue", "Forest", "Gold", "Kelly", 
            "Lavender_Blue", "Light_Violet", "Maroon", "Mauve", "Military_Green", "Mint", 
            "Mustard", "Natural", "Navy", "Peach", "Pink", "Red", "Royal_Purple", "Silver", 
            "Soft_Cream", "Solid_Athletic_Grey", "Steel_Blue", "Storm", "Tan", "Teal", 
            "Team_Purple", "Toast", "True_Royal", "Vintage_Black", "Vintage_White"
        ]
        
        for color in bella_colors:
            self.categories['t-shirt'].add_product({
                'style_number': '3001',
                'product_name': 'Bella + Canvas Jersey Tee',
                'color': color.replace("_", " "),
                'price': '$13.99',
                'material': '100% Airlume combed and ring-spun cotton',
                'weight': 'lightweight',
                'fit': 'retail fit',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'S-5XL',
                'features': [
                    'Airlume combed and ring-spun cotton',
                    'Pre-shrunk',
                    'Shoulder-to-shoulder taping',
                    'Tear away label'
                ],
                'images': {
                    'front': f'/productimages/3001/BELLA_+_CANVAS_3001_{color}_Front_High.jpg',
                    'back': f'/productimages/3001/BELLA_+_CANVAS_3001_{color}_Back_High.jpg'
                }
            })
            
        # Comfort Colors - Garment-Dyed Heavyweight T-Shirt
        comfort_colors = [
            "White", "Black", "Blossom", "Blue_Jean", "Butter", "Chalky_Mint", "Chambray", 
            "China_Blue", "Crimson", "Crunchberry", "Denim", "Flo_Blue", "Granite", "Grey", 
            "Ice_Blue", "Island_Green", "Island_Reef", "Lagoon", "Melon", "Neon_Pink", 
            "Orchid", "Pepper", "Royal_Caribe", "Seafoam", "Terracotta", "Topaz_Blue", 
            "True_Navy", "Violet", "Washed_Denim", "Watermelon"
        ]
        
        for color in comfort_colors:
            self.categories['t-shirt'].add_product({
                'style_number': '1717',
                'product_name': 'Comfort Colors - Garment-Dyed Heavyweight T-Shirt',
                'color': color.replace("_", " "),
                'price': '$15.46',
                'material': '100% ring-spun cotton',
                'weight': 'heavyweight',
                'fit': 'relaxed',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'S-5XL',
                'features': [
                    'Garment-dyed for that lived in feel',
                    'Almost no shrinkage',
                    'Made with OEKO-TEX certified low-impact dyes'
                ],
                'images': {
                    'front': f'/productimages/1717/Comfort_Colors_1717_{color}_Front_High.jpg',
                    'back': f'/productimages/1717/Comfort_Colors_1717_{color}_Back_High.jpg'
                }
            })
        
        # Long Sleeve Shirts category
        self.categories['long-sleeve'] = ProductCategory('Long Sleeve Shirts', claude_client=self.claude_client)
        
        # Gildan - Heavy Cotton Long Sleeve T-Shirt
        gildan_ls_colors = [
            "White", "Black", "Carolina_Blue", "Forest_Green", "Gold", "Irish_Green", 
            "Navy", "Purple", "Red", "Royal", "Sport_Grey"
        ]
        
        for color in gildan_ls_colors:
            self.categories['long-sleeve'].add_product({
                'style_number': '5400',
                'product_name': 'Gildan - Heavy Cotton Long Sleeve T-Shirt',
                'color': color.replace("_", " "),
                'price': '$14.17',
                'material': '100% cotton',
                'weight': 'heavyweight',
                'fit': 'classic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'S-3XL',
                'features': [
                    'Taped neck and shoulders for comfort and durability',
                    'Rib cuffs',
                    'Tear away label'
                ],
                'images': {
                    'front': f'/productimages/5400/5400_{color}_Front.jpg',
                    'back': f'/productimages/5400/5400_{color}_Back.jpg'
                }
            })
            
        # Sport-Tek Long Sleeve PosiCharge Competitor Tee
        sporttek_ls_colors = [
            {"display": "Atomic Blue", "filename": "ST350LS_Atomic Blue_Flat"},
            {"display": "Black", "filename": "ST350LS_black_flat"},
            {"display": "Carolina Blue", "filename": "ST350LS_Carolina Blue_Flat"},
            {"display": "Deep Red", "filename": "ST350LS_DEEP RED_Flat"},
            {"display": "Forest Green", "filename": "ST350LS_Forest Green_Flat"},
            {"display": "Gold", "filename": "ST350LS_gold_flat"},
            {"display": "Grey Concrete", "filename": "ST350LS_GREY CONCRETE_Flat"},
            {"display": "Grey Concrete Heather", "filename": "ST350LS_GREY CONCRETE HEATHER_Flat"},
            {"display": "Iron Grey", "filename": "ST350LS_Iron Grey_Flat"},
            {"display": "Iron Grey Heather", "filename": "ST350LS_IRON GREY HEATHER_Flat"},
            {"display": "Lime Shock", "filename": "ST350LS_Lime Shock_Flat"},
            {"display": "Maroon", "filename": "ST350LS_maroon_flat"},
            {"display": "Neon Orange", "filename": "ST350LS_Neon Orange_Flat"},
            {"display": "Neon Pink", "filename": "ST350LS_Neon Pink_Flat"},
            {"display": "Purple", "filename": "ST350LS_purple_flat"},
            {"display": "Royal", "filename": "ST350LS_Royal_Flat"},
            {"display": "Silver", "filename": "ST350LS_silver_flat"},
            {"display": "True Navy", "filename": "ST350LS_True Navy_Flat"},
            {"display": "True Red", "filename": "ST350LS_True Red_Flat"},
            {"display": "True Royal", "filename": "ST350LS_TRUE ROYAL_Flat"},
            {"display": "White", "filename": "ST350LS_white_flat"}
        ]
        
        for color in sporttek_ls_colors:
            self.categories['long-sleeve'].add_product({
                'style_number': 'ST350LS',
                'product_name': 'Sport-Tek Long Sleeve PosiCharge Competitor Tee',
                'color': color["display"],
                'price': '$14.99',
                'material': '100% polyester interlock',
                'weight': 'lightweight',
                'fit': 'athletic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'XS-4XL',
                'features': [
                    'Moisture-wicking',
                    'PosiCharge technology to lock in color',
                    'Removable tag for comfort and relabeling'
                ],
                'images': {
                    'front': f'/productimages/ST350LS/{color["filename"]}_Front.jpg',
                    'back': f'/productimages/ST350LS/{color["filename"]}_Back.jpg'
                }
            })
        
        # Hoodies category (maps to "Sweatshirt" in Claude)
        self.categories['hoodie'] = ProductCategory('Hoodies', claude_client=self.claude_client)
        
        # Hanes Ecosmart Hooded Sweatshirt
        hanes_hoodie_colors = [
            "White", "Black", "Ash", "Carolina_Blue", "Charcoal_Heather", "Deep_Forest", 
            "Deep_Red", "Deep_Royal", "Gold", "Heather_Navy", "Heather_Red", "Light_Blue", 
            "Light_Steel", "Maroon", "Navy", "Pale_Pink", "Smoke_Grey", "Teal"
        ]
        
        for color in hanes_hoodie_colors:
            self.categories['hoodie'].add_product({
                'style_number': 'P170',
                'product_name': 'Hanes Ecosmart Hooded Sweatshirt',
                'color': color.replace("_", " "),
                'price': '$19.40',
                'material': '50/50 cotton/polyester',
                'weight': 'midweight',
                'fit': 'standard',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'S-5XL',
                'features': [
                    'Patented, low-pill, high-stitch density PrintPro XP fleece',
                    'Dyed-to-match drawcord',
                    'Pouch pocket',
                    'Ribbed cuffs and waistband'
                ],
                'images': {
                    'front': f'/productimages/P170/Hanes_P170_{color}_Front_High.jpg',
                    'back': f'/productimages/P170/Hanes_P170_{color}_Back_High.jpg'
                }
            })
            
        # Augusta Sportswear 60/40 Fleece Hoodie
        augusta_hoodie_colors = [
            "White", "Black", "Carbon_Heather", "Charcoal_Heather", "Columbia_Blue", 
            "Dark_Green", "Graphite", "Kelly", "Maroon", "Navy", "Orange", "Power_Pink", 
            "Purple", "Red", "Royal", "Vegas_Gold"
        ]
        
        for color in augusta_hoodie_colors:
            self.categories['hoodie'].add_product({
                'style_number': '5414',
                'product_name': 'Augusta Sportswear 60/40 Fleece Hoodie',
                'color': color.replace("_", " "),
                'price': '$27.50',
                'material': '60/40 cotton/polyester athletic fleece',
                'weight': 'heavyweight',
                'fit': 'athletic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'S-L',
                'adult_sizes': 'S-5XL',
                'features': [
                    'Jersey lined hood',
                    'Drawcord in hood',
                    'Pouch pocket',
                    'Rib-knit cuffs and bottom band'
                ],
                'images': {
                    'front': f'/productimages/5414/Augusta_Sportswear_5414_{color}_Front_High.jpg',
                    'back': f'/productimages/5414/Augusta_Sportswear_5414_{color}_Back_High.jpg'
                }
            })
        
        # Crewneck sweatshirts
        self.categories['crewneck'] = ProductCategory('Crewneck Sweatshirts', claude_client=self.claude_client)
        
        # Gildan - Heavy Blend Sweatshirt
        gildan_crewneck_colors = [
            "White", "Black", "Dark_Heather", "Forest", "Maroon", "Navy", 
            "Red", "Royal", "Safety_Pink", "Sport_Grey"
        ]
        
        for color in gildan_crewneck_colors:
            self.categories['crewneck'].add_product({
                'style_number': '18000',
                'product_name': 'Gildan - Heavy Blend Sweatshirt',
                'color': color.replace("_", " "),
                'price': '$15.95',
                'material': '50/50 cotton/polyester',
                'weight': 'heavyweight',
                'fit': 'classic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'XS-XL',
                'adult_sizes': 'XS-5XL',
                'features': [
                    'Made with finer yarns and new MVS Air spinning technology',
                    '1x1 rib with spandex for enhanced stretch and recovery',
                    'Tear away label'
                ],
                'images': {
                    'front': f'/productimages/18000/Gildan_18000_{color}_Front_High.jpg',
                    'back': f'/productimages/18000/Gildan_18000_{color}_Back_High.jpg'
                }
            })
            
        # Sweatpants
        self.categories['sweatpants'] = ProductCategory('Sweatpants', claude_client=self.claude_client)
        
        # JERZEES - NuBlend Sweatpants
        jerzees_sweatpants_colors = [
            "Black", "Ash", "Forest_Green", "J._Navy", "Maroon", "Oxford", "Royal", "True_Red"
        ]
        
        for color in jerzees_sweatpants_colors:
            self.categories['sweatpants'].add_product({
                'style_number': '973M',
                'product_name': 'JERZEES - NuBlend Sweatpants',
                'color': color.replace("_", " "),
                'price': '$18.50',
                'material': '50/50 cotton/polyester',
                'weight': 'heavyweight',
                'fit': 'relaxed',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'S-XL',
                'adult_sizes': 'S-3XL',
                'features': [
                    'NuBlend pill-resistant fleece',
                    'High-stitch density for a smooth printing canvas',
                    'Double-needle stitched covered waistband with internal drawcord',
                    'Elastic bottom leg openings'
                ],
                'images': {
                    'front': f'/productimages/973M/JERZEES_973MR_{color}_Front_High.jpg',
                    'back': f'/productimages/973M/JERZEES_973MR_{color}_Back_High.jpg'
                }
            })
        
        # Map all products to make lookup easier by style number and color
        for category in self.categories.values():
            for product in category.products:
                style = product['style_number']
                color = product['color']
                key = f"{style}_{color}"
                self.product_data[key] = product