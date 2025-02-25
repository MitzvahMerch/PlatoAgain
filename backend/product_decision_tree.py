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
        
    def get_best_match(self, preferences: Dict) -> Optional[Dict]:
        """Find the best product match using a scoring system"""
        if not self.products:
            return None
            
        # Get AI color match if needed and available
        ai_matched_color = None
        if preferences.get('color') and self.claude_client:
            user_color = preferences.get('color')
            # Check if direct string matching will work
            exact_color_match = any(user_color.lower() in product.get('color', '').lower() for product in self.products)
            
            # If no exact match, try AI matching
            if not exact_color_match:
                available_colors = list(set(product.get('color', '') for product in self.products))
                try:
                    ai_matched_color = ProductDecisionTree.match_color_for_category(
                        user_color, 
                        available_colors, 
                        self.name,
                        self.claude_client
                    )
                    if ai_matched_color:
                        logger.info(f"AI matched '{user_color}' to '{ai_matched_color}' in category '{self.name}'")
                except Exception as e:
                    logger.error(f"Error in AI color matching: {str(e)}")
        
        # Score products rather than filtering
        scored_products = []
        
        for product in self.products:
            score = 0
            
            # Color matching (highest priority)
            if preferences.get('color'):
                if preferences['color'].lower() in product.get('color', '').lower():
                    score += 100  # Major boost for exact color match
                elif ai_matched_color and ai_matched_color == product.get('color'):
                    score += 90   # Good boost for AI-matched color
                elif preferences.get('color') and not ai_matched_color:
                    # Skip products that don't match explicitly requested color if no AI match found
                    continue
                
            # Price scoring - for budget options, prioritize cheaper products
            if preferences.get('price') == 'budget-friendly':
                price_val = float(product.get('price', '$100').replace('$', ''))
                # Inverse score based on price - cheaper gets higher score
                score += 50 * (1 - (price_val / 30))  # Assuming $30 is max price
                
            # Material/softness scoring
            if preferences.get('material') and preferences['material'].lower() in product.get('material', '').lower():
                score += 20
            # If soft was mentioned (parsed as material)
            elif preferences.get('material') == 'soft':
                if 'cotton' in product.get('material', '').lower() or 'ring-spun' in product.get('material', '').lower():
                    score += 15
                    
            # Weight preferences
            if preferences.get('weight') and preferences['weight'].lower() in product.get('weight', '').lower():
                score += 10
                
            # Fit preferences
            if preferences.get('fit') and preferences['fit'].lower() in product.get('fit', '').lower():
                score += 10
                
            # Size requirements
            if preferences.get('size') == 'youth' and product.get('has_youth_sizes'):
                score += 15
                
            # Brand preferences
            if preferences.get('brand') and preferences['brand'].lower() in product.get('product_name', '').lower():
                score += 15
                
            scored_products.append((product, score))
        
        # Sort by score, highest first
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        if scored_products:
            top_products = [(p[0]['product_name'], p[0]['color'], p[1]) for p in scored_products[:3] if len(scored_products) >= 3]
            logger.info(f"Top scored products: {top_products}")
        
        # Return highest scoring product or first product if none scored
        if scored_products:
            return scored_products[0][0]
            
        # If no matches (due to color filtering), return None
        return None


class ProductDecisionTree:
    """Decision tree for product selection"""
    
    def __init__(self, claude_client=None):
        self.categories = {}
        self.product_data = {}
        self.claude_client = claude_client
        self.init_product_data()
    
    @staticmethod
    def match_color_for_category(user_color: str, available_colors: List[str], category_name: str, claude_client) -> Optional[str]:
        """Use Claude to match a user's color description to available colors ONLY within a specific category"""
        
        if not user_color or not available_colors or not claude_client:
            return None
            
        # Format colors as a comma-separated list
        color_list = ", ".join(available_colors)
        
        # Create a category-specific prompt for Claude
        color_matching_prompt = [
            {"role": "user", "content": f"""<instructions>
            You are a color matching expert for a custom apparel print shop. Match the customer's color description 
            to the most similar color from our available options for {category_name}s.
            
            Available colors for {category_name}s: {color_list}
            
            Rules:
            1. ONLY consider colors available for {category_name}s
            2. Return EXACTLY ONE color from the list provided, no explanation
            3. If no close match exists, return "NO_MATCH"
            4. Do not invent new colors or modify existing ones
            </instructions>"""},
            {"role": "user", "content": f"Find the closest match to: {user_color}"}
        ]
        
        # Call Claude API
        try:
            matched_color = claude_client.call_api(color_matching_prompt, temperature=0.2)
            matched_color = matched_color.strip()
            
            # Validate the response
            if matched_color in available_colors:
                logger.info(f"Successfully matched user color '{user_color}' to catalog color '{matched_color}' in {category_name}")
                return matched_color
            elif matched_color == "NO_MATCH":
                logger.info(f"No match found for user color '{user_color}' in {category_name}")
                return None
            else:
                logger.warning(f"Invalid color match result: '{matched_color}' not in available colors")
                return None
        except Exception as e:
            logger.error(f"Error in color matching: {str(e)}")
            return None
    
    def parse_sonar_analysis(self, analysis_text: str) -> Dict:
        """Parse the structured output from Sonar's analysis"""
        preferences = {}
        
        # Define patterns to extract each preference
        patterns = {
            'garment': r'Garment Type:\s*([^\n]+)',
            'brand': r'Brand Preferences:\s*([^\n]+)',
            'material': r'Material Preferences:\s*([^\n]+)',
            'color': r'Color Preferences:\s*([^\n]+)',
            'weight': r'Weight Preferences:\s*([^\n]+)',
            'fit': r'Fit Preferences:\s*([^\n]+)',
            'size': r'Size Requirements:\s*([^\n]+)',
            'price': r'Price Points:\s*([^\n]+)'
        }
        
        # Extract each preference
        for key, pattern in patterns.items():
            match = re.search(pattern, analysis_text)
            if match and "No specific" not in match.group(1):
                preferences[key] = match.group(1).strip()
        
        logger.info(f"Parsed preferences: {preferences}")
        return preferences
        
    def get_category_from_garment(self, garment_type: str) -> str:
        """Map garment type to category"""
        garment_type = garment_type.lower()
        
        if 't-shirt' in garment_type or 'tee' in garment_type:
            return 't-shirt'
        elif 'long sleeve' in garment_type:
            return 'long-sleeve'
        elif 'hoodie' in garment_type or 'hooded' in garment_type:
            return 'hoodie'
        elif 'sweatshirt' in garment_type or 'crewneck' in garment_type:
            return 'crewneck'
        elif 'sweatpant' in garment_type or 'jogger' in garment_type:
            return 'sweatpants'
        
        # Default to t-shirt if no match
        return 't-shirt'
    
    def select_product(self, query: str, sonar_analysis: str) -> Optional[Dict]:
        """
        Select a product based on user query and Sonar analysis.
        Returns product details dictionary.
        """
        try:
            # Parse the structured Sonar analysis
            preferences = self.parse_sonar_analysis(sonar_analysis)
            
            # Determine product category from garment type
            category = self.get_category_from_garment(preferences.get('garment', 't-shirt'))
            
            logger.info(f"Category identified: {category}")
            logger.info(f"Preferences extracted: {preferences}")
            
            # Try to find a match in the primary category
            if category in self.categories:
                best_match = self.categories[category].get_best_match(preferences)
                if best_match:
                    logger.info(f"Selected product: {best_match['product_name']} in {best_match['color']}")
                    return best_match
            
            # If no match in primary category, try other categories
            for cat_name, category_obj in self.categories.items():
                if cat_name != category:
                    best_match = category_obj.get_best_match(preferences)
                    if best_match:
                        logger.info(f"Selected product from alternate category {cat_name}: {best_match['product_name']} in {best_match['color']}")
                        return best_match
            
            # If color is specified but no matches, try again without strict color matching
            if preferences.get('color'):
                logger.info(f"No matches for color '{preferences['color']}', trying without strict color matching")
                color = preferences.pop('color')  # Remove color to try without it
                
                # Try primary category first
                if category in self.categories:
                    products = self.categories[category].products
                    if products:
                        # Sort by price if budget-friendly
                        if preferences.get('price') == 'budget-friendly':
                            products_copy = products.copy()
                            products_copy.sort(key=lambda p: float(p.get('price', '$100').replace('$', '')))
                            logger.info(f"Selected cheapest product: {products_copy[0]['product_name']} in {products_copy[0]['color']}")
                            return products_copy[0]
                        else:
                            logger.info(f"Selected default product: {products[0]['product_name']} in {products[0]['color']}")
                            return products[0]
            
            # Last resort - return first t-shirt
            logger.info("No suitable match found, defaulting to first t-shirt")
            return self.categories['t-shirt'].products[0] if 't-shirt' in self.categories else None
            
        except Exception as e:
            logger.error(f"Error in product selection: {str(e)}")
            # Default product if there's an error
            if self.categories.get('t-shirt') and self.categories['t-shirt'].products:
                return self.categories['t-shirt'].products[0]
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
        self.categories['long-sleeve'] = ProductCategory('Long Sleeve Shirts')
        
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
        
        # Hoodies/Sweatshirts category
        self.categories['hoodie'] = ProductCategory('Hoodies')
        
        # Hanes - Ecosmart Hooded Sweatshirt
        hanes_hoodie_colors = [
            "White", "Black", "Ash", "Carolina_Blue", "Charcoal_Heather", "Deep_Forest", 
            "Deep_Red", "Deep_Royal", "Gold", "Heather_Navy", "Heather_Red", "Light_Blue", 
            "Light_Steel", "Maroon", "Navy", "Pale_Pink", "Smoke_Grey", "Teal"
        ]
        
        for color in hanes_hoodie_colors:
            self.categories['hoodie'].add_product({
                'style_number': 'P170',
                'product_name': 'Hanes - Ecosmart Hooded Sweatshirt',
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
        self.categories['crewneck'] = ProductCategory('Crewneck Sweatshirts')
        
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
        self.categories['sweatpants'] = ProductCategory('Sweatpants')
        
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