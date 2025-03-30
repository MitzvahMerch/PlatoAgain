import logging
from typing import Dict, List, Optional, Tuple
import os
import re
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

# =============================================================================
# 1. Comprehensive Semantic Color Map
# =============================================================================
SEMANTIC_COLOR_MAP = {
    # Blues
    "blue": ["Carolina Blue", "Light Blue", "Atomic Blue", "Tropic Blue", "Royal", "True Royal", "True Royal Heather", "Heather_Navy", "Pacific_Blue", "True Navy", "Navy", "Columbia Blue", "Blue Jean", "Washed Denim", "Power Blue", "Vintage Heather Blue", "Chambray", "Topaz Blue", "Denim", "Vintage Heather Navy", "Royal Caribe", "China Blue", "Flo Blue", "Ice Blue", "Scuba Blue", "Aquatic Blue", "California Blue"],
    "light blue": ["Carolina Blue", "Light Blue", "Power Blue", "Chambray", "Ice Blue"],
    "sky blue": ["Carolina Blue", "Columbia Blue", "Pacific_Blue", "Power Blue"],
    "baby blue": ["Carolina Blue", "Light Blue", "Pacific_Blue",],
    "bright blue": ["Atomic Blue", "Royal Caribe", "Scuba Blue", "Power Blue"],
    "medium blue": ["Royal", "True Royal", "True Royal Heather", "Blue Jean", "Pacific_Blue", "Flo Blue"],
    "deep blue": ["True Navy", "Navy", "China Blue", "Denim"],
    "dark blue": ["True Navy", "Navy", "Heather_Navy", "Denim"],
    "navy": ["True Navy", "Navy", "Heather_Navy", "J Navy", "Vintage Heather Navy"],
    "navy blue": ["True Navy", "Navy", "Heather_Navy", "J Navy", "Vintage Heather Navy"],
    "royal blue": ["Royal", "True Royal", "Royal Caribe"],
    "teal": ["Tropic Blue", "Teal", "Topaz Blue", "California Blue", "Scuba Blue"],
    "turquoise": ["Atomic Blue", "Tropic Blue", "Teal", "Scuba Blue", "California Blue"],
    "aqua": ["Atomic Blue", "Tropic Blue", "Aquatic Blue", "Pacific_Blue","Scuba Blue", "Power Blue"],
    "azure": ["Carolina Blue", "Columbia Blue", "Pacific_Blue"],
    
    # Reds
    "red": ["True Red", "Red", "Cardinal", "Maroon", "Burgundy", "Deep Red", "Crimson", "Cardinal", "Poppy", "Watermelon", "Crunchberry", "Vintage Heather Red", "Vintage Heather Maroon"],
    "light red": ["True Red", "Red", "Watermelon", "Crunchberry"],
    "bright red": ["True Red", "Red", "Cardinal"],
    "dark red": ["Maroon", "Cardinal", "Burgundy", "Deep Red"],
    "maroon": ["Maroon"],
    "burgundy": ["Burgundy", "Deep Red"],
    "wine": ["Maroon", "Burgundy"],
    "crimson": ["Cardinal", "Deep Red", "Crimson"],
    "scarlet": ["True Red", "Red"],
    "ruby": ["Deep Red", "Maroon", "Burgundy"],
    
    # Greens
    "green": ["Mint", "Kelly Green", "Kelly", "Lime Shock", "Neon Green", "Forest Green", "Dark Green", "Deep Forest", "Chalky Mint", "Irish Green", "Military Green", "Island Green", "Island Reef", "Kiwi", "Seafoam", "Cool Mint", "Jade"],
    "light green": ["Mint", "Chalky Mint", "Cool Mint", "Island Reef", "Seafoam"],
    "bright green": ["Kelly Green", "Kelly", "Lime Shock", "Neon Green", "Kiwi", "Island Green"],
    "dark green": ["Forest Green", "Dark Green", "Deep Forest"],
    "forest green": ["Forest Green", "Deep Forest"],
    "mint": ["Mint", "Chalky Mint", "Cool Mint"],
    "kelly green": ["Kelly Green", "Kelly", "Irish Green"],
    "lime": ["Lime Shock", "Neon Green", "Safety Green"],
    "olive": ["Military Green"],
    "jade": ["Jade", "Island Green"],
    "seafoam": ["Seafoam", "Island Reef"],
    
    # Yellows
    "yellow": ["Butter", "Neon Yellow", "Gold", "Power Yellow", "Vegas Gold", "Mustard", "Island Yellow"],
    "light yellow": ["Butter", "Neon Yellow"],
    "bright yellow": ["Neon Yellow", "Island Yellow", "Power Yellow"],
    "gold": ["Gold", "Vegas Gold"],
    "mustard": ["Mustard", "Gold"],
    
    # Oranges
    "orange": ["Melon", "Peach", "Neon Orange", "Deep Orange", "Safety Orange", "Texas Orange", "Burnt Orange", "Tennessee Orange", "Orange"],
    "light orange": ["Melon", "Peach"],
    "bright orange": ["Neon Orange", "Deep Orange", "Safety Orange", "Orange"],
    "dark orange": ["Texas Orange", "Burnt Orange", "Tennessee Orange"],
    "safety orange": ["Safety Orange", "Neon Orange"],
    "peach": ["Peach", "Melon"],
    
    # Purples
    "purple": ["Lavender", "Orchid", "Light Violet", "Violet", "Purple", "Royal Purple", "Deep Purple", "Team Purple", "Mauve"],
    "light purple": ["Lavender", "Orchid", "Light Violet"],
    "bright purple": ["Violet", "Purple", "Royal Purple"],
    "dark purple": ["Deep Purple", "Team Purple"],
    "lavender": ["Lavender", "Light Violet"],
    "violet": ["Violet", "Purple", "Orchid"],
    "indigo": ["Deep Purple", "Team Purple"],
    "lilac": ["Lavender", "Light Violet", "Orchid"],
    "mauve": ["Mauve"],
    
    # Pinks
    "pink": ["Classic Pink", "Pale Pink", "Blossom", "Neon Pink", "Cyber Pink", "Power Pink", "Berry", "Pink", "Safety Pink"],
    "light pink": ["Classic Pink", "Pale Pink", "Blossom", "Pink"],
    "bright pink": ["Neon Pink", "Cyber Pink", "Power Pink", "Safety Pink"],
    "dark pink": ["Cyber Pink", "Berry"],
    "hot pink": ["Neon Pink", "Cyber Pink", "Power Pink"],
    "magenta": ["Cyber Pink", "Berry", "Power Pink"],
    
    # Grays
    "gray": ["Silver", "Ash", "Light Steel", "Athletic Heather", "Grey Concrete", "Silver_Grey", "Grey Concrete Heather", "Greystone", "Iron Grey Heather", "Sport Grey", "Charcoal Grey", "Iron Grey", "Carbon Heather", "Smoke Grey", "Graphite", "Dark Grey", "Heather_Steel", "Granite", "Grey", "Pepper", "Asphalt", "Oxford", "Storm", "Dark Heather"],
    "grey": ["Silver", "Ash", "Light Steel", "Athletic Heather", "Grey Concrete", "Silver_Grey", "Grey Concrete Heather","Greystone", "Iron Grey Heather", "Sport Grey", "Charcoal Grey", "Iron Grey", "Carbon Heather", "Smoke Grey", "Graphite", "Dark Grey", "Heather_Steel", "Granite", "Grey", "Pepper", "Asphalt", "Oxford", "Storm", "Dark Heather"],
    "light gray": ["Silver", "Ash", "Light Steel", "Heather_Steel", "Athletic Heather", "Silver_Grey", "Greystone", "Solid Athletic Grey"],
    "medium gray": ["Grey Concrete", "Grey Concrete Heather", "Heather_Steel", "Silver_Grey", "Iron Grey Heather", "Sport Grey", "Greystone", "Grey", "Storm", "Oxford"],
    "dark gray": ["Charcoal Grey", "Iron Grey", "Carbon Heather", "Smoke Grey", "Graphite", "Dark Grey", "Pepper", "Asphalt", "Dark Heather"],
    "silver": ["Silver, Greystone", "Heather_Steel", "Power Yellow", "Silver_Grey"],
    "charcoal": ["Charcoal Grey", "Graphite", "Iron Grey", "Carbon Heather", "Smoke Grey"],
    "slate": ["Steel Blue", "Blue Storm"],
    
    # Browns
    "brown": ["Tan", "Toast", "Soft Cream", "Saddle", "Nut Brown", "Brown", "Chocolate", "Dark Brown", "Coffee"],
    "light brown": ["Tan", "Toast", "Soft Cream", "Brown"],
    "medium brown": ["Saddle", "Nut Brown", "Brown"],
    "dark brown": ["Chocolate", "Dark Brown", "Coffee", "Brown"],
    "tan": ["Tan", "Soft Cream"],
    "beige": ["Natural", "Soft Cream", "Tan"],
    
    # Whites
    "white": ["White", "Natural", "Vintage White"],
    "off-white": ["Natural", "Vintage White", "Soft Cream"],
    "cream": ["Soft Cream", "Natural", "Vintage White", "Butter"],
    "ivory": ["Natural", "Vintage White"],
    
    # Blacks
    "black": ["Black", "Vintage Black", "Black Heather"],
    "jet black": ["Black"],
    
    # Other
    "coral": ["Watermelon", "Crunchberry"],
    "copper": ["Toast", "Terracotta"],
    "khaki": ["Tan"],
    "rust": ["Burnt Orange", "Texas Orange", "Tennessee Orange", "Terracotta"],
    "sage": ["Mint", "Seafoam", "Chalky Mint", "Cool Mint"],
    "terracotta": ["Terracotta"]
}

# =============================================================================
# 2. Color Family Classification & Categorization System
# =============================================================================
COLOR_FAMILIES = {
    "blue": {
        "hue_range": (180, 250),  # Cyan to Indigo
        "modifiers": {
            "light": {"lightness_min": 65},
            "medium": {"lightness_range": (40, 65)},
            "dark": {"lightness_max": 40},
            "bright": {"saturation_min": 70},
            "pale": {"saturation_max": 40, "lightness_min": 70},
            "dull": {"saturation_max": 40},
            "vintage": {}
        }
    },
    "green": {
        "hue_range": (90, 180),
        "modifiers": {
            "light": {"lightness_min": 60},
            "dark": {"lightness_max": 40},
            "bright": {"saturation_min": 70},
            "pale": {"saturation_max": 40, "lightness_min": 70},
            "olive": {"saturation_range": (20, 60), "lightness_range": (20, 50)}
        }
    },
    "yellow": {
        "hue_range": (40, 90),
        "modifiers": {
            "light": {"lightness_min": 80},
            "pale": {"saturation_max": 50, "lightness_min": 80},
            "golden": {"saturation_range": (50, 90), "lightness_range": (40, 60)}
        }
    },
    "orange": {
        "hue_range": (15, 40),
        "modifiers": {
            "light": {"lightness_min": 70},
            "dark": {"lightness_max": 50},
            "bright": {"saturation_min": 80}
        }
    },
    "red": {
        "hue_range": (350, 15),  # Note: wraps around 0
        "modifiers": {
            "light": {"lightness_min": 65},
            "dark": {"lightness_max": 40},
            "bright": {"saturation_min": 80},
            "burgundy": {"lightness_range": (20, 40), "saturation_range": (50, 80)}
        }
    },
    "purple": {
        "hue_range": (250, 320),
        "modifiers": {
            "light": {"lightness_min": 65},
            "dark": {"lightness_max": 40},
            "bright": {"saturation_min": 70},
            "lavender": {"lightness_min": 70, "saturation_range": (20, 50)}
        }
    },
    "pink": {
        "hue_range": (320, 350),
        "modifiers": {
            "light": {"lightness_min": 75},
            "dark": {"lightness_range": (40, 60), "saturation_min": 50},
            "hot": {"saturation_min": 80, "lightness_min": 60}
        }
    },
    "gray": {
        "saturation_max": 10,
        "modifiers": {
            "light": {"lightness_min": 70},
            "medium": {"lightness_range": (40, 70)},
            "dark": {"lightness_max": 40},
            "silver": {"lightness_min": 70}
        }
    },
    "brown": {
        "hue_range": (0, 40),
        "saturation_range": (10, 60),
        "lightness_range": (15, 60),
        "modifiers": {
            "light": {"lightness_min": 50},
            "dark": {"lightness_max": 30}
        }
    },
    "white": {
        "lightness_min": 85,
        "saturation_max": 15,
        "modifiers": {
            "pure": {"lightness_min": 95, "saturation_max": 5},
            "off": {"lightness_range": (85, 95), "saturation_range": (5, 15)}
        }
    },
    "black": {
        "lightness_max": 20,
        "saturation_max": 40,
        "modifiers": {
            "jet": {"lightness_max": 10},
            "off": {"lightness_range": (15, 25)}
        }
    }
}

# =============================================================================
# 3. HSL Color Conversion and Distance Functions
# =============================================================================
def hex_to_hsl(hex_color: str) -> Tuple[int, float, float]:
    """Convert hex color to HSL (Hue, Saturation, Lightness)."""
    logger.info(f"Converting hex color {hex_color} to HSL")
    
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin
    h = 0
    if delta != 0:
        if cmax == r:
            h = ((g - b) / delta) % 6
        elif cmax == g:
            h = (b - r) / delta + 2
        else:
            h = (r - g) / delta + 4
    h = round(h * 60)
    if h < 0:
        h += 360
    l = (cmax + cmin) / 2
    s = 0
    if delta != 0:
        s = delta / (1 - abs(2 * l - 1))
    s *= 100
    l *= 100
    
    logger.info(f"Hex {hex_color} converted to HSL: H={h}, S={s:.2f}, L={l:.2f}")
    return h, s, l

def hsl_distance(hsl1: Tuple[int, float, float], hsl2: Tuple[int, float, float]) -> float:
    """Calculate perceptual distance between two HSL colors."""
    h1, s1, l1 = hsl1
    h2, s2, l2 = hsl2
    h_diff = min(abs(h1 - h2), 360 - abs(h1 - h2)) / 180.0
    s_diff = abs(s1 - s2) / 100.0
    l_diff = abs(l1 - l2) / 100.0
    h_weight = 1.0
    s_weight = 0.8
    l_weight = 1.5
    avg_s = (s1 + s2) / 2.0
    h_weight = h_weight * (avg_s / 100.0) + 0.3
    distance = ((h_weight * h_diff) ** 2 +
                (s_weight * s_diff) ** 2 +
                (l_weight * l_diff) ** 2) ** 0.5
    return distance

# =============================================================================
# 4. Color Family Determination Functions
# =============================================================================
def check_sl_constraints(properties: Dict, s: float, l: float) -> bool:
    """Check if saturation and lightness values meet the constraints defined in properties."""
    if "saturation_min" in properties and s < properties["saturation_min"]:
        return False
    if "saturation_max" in properties and s > properties["saturation_max"]:
        return False
    if "saturation_range" in properties:
        min_s, max_s = properties["saturation_range"]
        if not (min_s <= s <= max_s):
            return False
    if "lightness_min" in properties and l < properties["lightness_min"]:
        return False
    if "lightness_max" in properties and l > properties["lightness_max"]:
        return False
    if "lightness_range" in properties:
        min_l, max_l = properties["lightness_range"]
        if not (min_l <= l <= max_l):
            return False
    return True

def determine_color_family(hex_color: str) -> str:
    """Determine which color family a hex color belongs to based on HSL values."""
    h, s, l = hex_to_hsl(hex_color)
    if s < 10:
        if l > 85:
            return "white"
        elif l < 20:
            return "black"
        else:
            return "gray"
    for family, properties in COLOR_FAMILIES.items():
        if family in ["white", "black", "gray"]:
            continue
        if "hue_range" in properties:
            min_hue, max_hue = properties["hue_range"]
            if min_hue > max_hue:
                if h >= min_hue or h <= max_hue:
                    if check_sl_constraints(properties, s, l):
                        return family
            else:
                if min_hue <= h <= max_hue:
                    if check_sl_constraints(properties, s, l):
                        return family
        elif check_sl_constraints(properties, s, l):
            return family
    if 0 <= h < 15 or h >= 350:
        return "red"
    elif 15 <= h < 40:
        return "orange"
    elif 40 <= h < 70:
        return "yellow"
    elif 70 <= h < 150:
        return "green"
    elif 150 <= h < 200:
        return "teal"
    elif 200 <= h < 270:
        return "blue"
    elif 270 <= h < 350:
        return "purple"
    return "unknown"

def determine_color_modifiers(hex_color: str, family: str) -> List[str]:
    """Determine which color modifiers apply to a color within its family."""
    h, s, l = hex_to_hsl(hex_color)
    if family not in COLOR_FAMILIES:
        return []
    family_props = COLOR_FAMILIES[family]
    if "modifiers" not in family_props:
        return []
    modifiers = []
    for modifier_name, constraints in family_props["modifiers"].items():
        if check_sl_constraints(constraints, s, l):
            modifiers.append(modifier_name)
    priority_order = ["light", "medium", "dark", "bright", "pale", "dull"]
    modifiers.sort(key=lambda m: priority_order.index(m) if m in priority_order else 999)
    return modifiers

# =============================================================================
# 5. The Main Color Matching Function & Product Decision Tree
# =============================================================================
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
    """Decision tree for product selection with color-based optimization"""
    
    # Existing color mapping dictionary for hex codes (unchanged)
    COLOR_HEX_MAP = {
        # JERZEES T-Shirt Colors (29MR)
        "White": "#EBEBE3",
        "Black": "#292A2E",
        "Aquatic_Blue": "#4DB7D1",
        "Ash": "#BBB9BA",
        "Athletic_Heather": "#A9ADB0",
        "Black_Heather": "#4C4B50",
        "Burnt_Orange": "#DB431A",
        "California_Blue": "#32B2BB",
        "Cardinal": "#6B1434",
        "Charcoal_Grey": "#3C3C3E",
        "Classic_Pink": "#E4C1C8",
        "Columbia_Blue": "#5083B0",
        "Cool_Mint": "#95E4C7",
        "Cyber_Pink": "#AB386F",
        "Deep_Purple": "#3F2D67",
        "Forest_Green": "#2D3832",
        "Gold": "#FEAF2C",
        "Irish_Green_Heather": "#15AD7E",
        "Island_Yellow": "#FFB919",
        "J._Navy": "#303344",
        "Jade": "#028889",
        "Kelly": "#538A63",
        "Kiwi": "#80C260",
        "Light_Blue": "#B2C6E9",
        "Maroon": "#4E1C39",
        "Military_Green": "#5E6048",
        "Neon_Green": "#C1FE97",
        "Neon_Pink": "#FF6B9B",
        "Neon_Yellow": "#F1E85F",
        "Oxford": "#938F90",
        "Royal": "#1F3A67",
        "Safety_Green": "#CBFA7A",
        "Safety_Orange": "#FF7630",
        "Scuba_Blue": "#5DD2CC",
        "Silver": "#CECAC9",
        "Tennessee_Orange": "#FF6421",
        "True_Red": "#A9102C",
        "Vintage_Heather_Blue": "#585C68",
        "Vintage_Heather_Maroon": "#723642",
        "Vintage_Heather_Navy": "#4A4C58",
        "Vintage_Heather_Red": "#AC4D53",
        "Violet": "#7A70B9",
        
        # Sport-Tek Colors (ST350)
        "Atomic Blue": "#11A2BF",
        "Black": "#282A29",
        "Carolina Blue": "#77A8D3",
        "DEEP RED": "#972336",
        "Deep Orange": "#D75D38",
        "Forest Green": "#284330",
        "Grey Concrete Heather": "#949F9B",
        "Grey Concrete": "#7F8487",
        "Iron Grey Heather": "#75797C",
        "Iron Grey": "#535456",
        "Kelly Green": "#0E7F51",
        "Lime Shock": "#BADC52",
        "Neon Orange": "#FA7228",
        "Neon Pink": "#FD589A",
        "Neon Yellow": "#E9FA00",
        "Royal": "#244D81",
        "Texas Orange": "#AC572E",
        "Tropic Blue": "#0C96A3",
        "True Navy": "#31384A",
        "True Red": "#BC1830",
        "True Royal Heather": "#5B80AA",
        "cardinal": "#62292F",
        "gold": "#FEC144",
        "maroon": "#502632",
        "purple": "#513E80",
        "silver": "#B5B7B2",
        "white": "#E9EDF6",
        
        # Bella + Canvas Jersey Tee (3001)
        "Ash": "#ECEBF0",
        "Asphalt": "#545454",
        "Berry": "#EC4A7B",
        "Black": "#191516",
        "Blue_Storm": "#768183",
        "Cardinal": "#6C1D23",
        "Carolina_Blue": "#84AFE2",
        "Dark_Grey": "#323232",
        "Dusty_Blue": "#BAD0C4",
        "Forest": "#17322B",
        "Gold": "#FFB72D",
        "Kelly": "#036431",
        "Lavender_Blue": "#909FBE",
        "Light_Violet": "#C1AFBD",
        "Maroon": "#521117",
        "Mauve": "#BE7D7B",
        "Military_Green": "#6D6854",
        "Mint": "#A9D5C6",
        "Mustard": "#E6A645",
        "Natural": "#DDDAC7",
        "Navy": "#272435",
        "Peach": "#F6C8B1",
        "Pink": "#D8B3BA",
        "Red": "#CE0120",
        "Royal_Purple": "#98629C",
        "Silver": "#D8D7D3",
        "Soft_Cream": "#F0D6B3",
        "Solid_Athletic_Grey": "#C9C5C2",
        "Steel_Blue": "#667079",
        "Storm": "#978D96",
        "Tan": "#CBBBAB",
        "Teal": "#49C9BC",
        "Team_Purple": "#342256",
        "Toast": "#CC8241",
        "True_Royal": "#054FAE",
        "Vintage_Black": "#261E1C",
        "Vintage_White": "#EEE6E3",
        "White": "#F0EFF4",
        
        # Comfort Colors T-Shirt (1717)
         "Black": "#232323",
         "Blossom": "#F7D5E5",
         "Blue_Jean": "#64738A",
         "Butter": "#FFE4AF",
         "Chalky_Mint": "#A4E1DC",
         "Chambray": "#CEE0EC",
         "China_Blue": "#425073",
         "Crimson": "#BB5A65",
         "Crunchberry": "#E77A91",
         "Denim": "#505362",
         "Flo_Blue": "#7591D2",
         "Granite": "#A5A6AA",
         "Grey": "#9B9391",
         "Ice_Blue": "#7898A7",
         "Island_Green": "#00C1A2",
         "Island_Reef": "#B0E2C9",
         "Lagoon": "#74CDDD",
         "Melon": "#FE8D4B",
         "Neon_Pink": "#FF84B9",
         "Orchid": "#DFCEDE",
         "Pepper": "#505052",
         "Royal_Caribe": "#159ADB",
         "Seafoam": "#75AEA7",
         "Terracotta": "#FA9581",
         "Topaz_Blue": "#017282",
         "True_Navy": "#222C45",
         "Violet": "#9486C1",
         "Washed_Denim": "#8EA2BD",
         "Watermelon": "#EF767F",
         "White": "#F2F1F6",
         
         # Gildan Crewneck (18000)
         "Black": "#212226",
         "Dark_Heather": "#444348",
         "Forest": "#2F4038",
         "Maroon": "#6B3241",
         "Navy": "#282D41",
         "Red": "#D92E40",
         "Royal": "#2B61AB",
         "Safety_Pink": "#FF84A6",
         "Sport_Grey": "#A7A6AE",
         "White": "#E9E9E1",
         
         # Gildan Long Sleeve (5400)
         "Black": "#292D30",
         "Carolina_Blue": "#7AA1DA",
         "Forest_Green": "#383F37",
         "Gold": "#E2A23E",
         "Irish_Green": "#4C975E",
         "Navy": "#333647",
         "Purple": "#443169",
         "Red": "#AF2C32",
         "Royal": "#2368B5",
         "Sport_Grey": "#A6A6A6",
         "White": "#E7E6EB",
         
         # Augusta Hoodie (5414)
         "Black": "#22222A",
         "Carbon_Heather": "#47484C",
         "Charcoal_Heather": "#999B9A",
         "Columbia_Blue": "#679CD0",
         "Dark_Green": "#1B5338",
         "Graphite": "#7D7C81",
         "Kelly": "#068957",
         "Maroon": "#5C1F31",
         "Navy": "#30324B",
         "Orange": "#E45825",
         "Power_Pink": "#C31D8B",
         "Purple": "#463988",
         "Red": "#C9233B",
         "Royal": "#3F5AA9",
         "Vegas_Gold": "#C8B477",
         "White": "#D8DCDD",
         
         # JERZEES Sweatpants (973M)
         "Ash": "#C8C3C9",
         "Athletic_Heather": "#A19D9C",
         "Black": "#222224",
         "Black_Heather": "#2E2E30",
         "Forest_Green": "#202F28",
         "J._Navy": "#2C2F40",
         "Maroon": "#501A2A",
         "Oxford": "#858182",
         "Royal": "#1C3259",
         "True_Red": "#980F29",
         "White": "#D6D6D8",
         
         # Hanes Hoodie (P170)
         "Ash": "#DFDFDF",
         "Black": "#2A282B",
         "Carolina_Blue": "#7AA2E0",
         "Charcoal_Heather": "#55545A",
         "Deep_Forest": "#404D46",
         "Deep_Red": "#950135",
         "Deep_Royal": "#364682",
         "Gold": "#E39E27",
         "Heather_Navy": "#393D58",
         "Heather_Red": "#E6425B",
         "Light_Blue": "#B4D0E8",
         "Light_Steel": "#C3C1C4",
         "Maroon": "#581D23",
         "Navy": "#393E51",
         "Pale_Pink": "#F1D3DB",
         "Smoke_Grey": "#4E4C51",
         "Teal": "#04A2C9",
         "White": "#F5F6F8",
         
         # Sport-Tek Long Sleeve (ST350LS)
         "Atomic Blue": "#1EA8CC",
         "Carolina Blue": "#80C0EC",
         "DEEP RED": "#921E31",
         "Forest Green": "#394F42",
         "GREY CONCRETE HEATHER": "#979A93",
         "GREY CONCRETE": "#9B9E97",
         "IRON GREY HEATHER": "#7A7E7D",
         "Iron Grey": "#575755",
         "Lime Shock": "#9FD015",
         "Neon Orange": "#F96446",
         "Neon Pink": "#F9529A",
         "Royal": "#254E82",
         "TRUE ROYAL": "#124E94",
         "True Navy": "#2B3245",
         "True Red": "#BF2A3D",
         "black": "#333333",
         "gold": "#FCB132",
         "maroon": "#712F39",
         "purple": "#523C91",
         "silver": "#D5DBDB",
         "white": "#E8E8E8",

        
        # AllPro Polo Colors (41800)
        "Black": "#222222",
        "Carolina_Blue": "#8BBAD8",
        "Forest_Green": "#314838",
        "Greystone": "#92938B",
        "Heather_Navy": "#6D7C93",
        "Heather_Steel": "#6F747A",
        "Maroon": "#5E2A36",
        "Navy": "#232C3D",
        "Pacific_Blue": "#2E718E",
        "Red": "#BC2430",
        "Royal": "#1E388C",
        "White": "#E8ECEF",

        # Gildan Polo Colors (8800)
        "Black": "#202123",
        "Gold": "#F4A73B",
        "Light_Blue": "#C2D3E3", 
        "Maroon": "#692C3C",
        "Navy": "#2E354F",
        "Red": "#E9283D",
        "Royal": "#285DA9",
        "Sport_Grey": "#C4C3CB",
        "White": "#EDEEF3",

        # JERZEES Hoodie Colors (996MR)
        "Ash": "#E2DDE3",
        "Athletic_Heather": "#BCBCC4",
        "Black": "#242328",
        "Black_Heather": "#525055",
        "Burnt_Orange": "#E44B22",
        "Charcoal_Grey": "#4A484D",
        "Cyber_Pink": "#C2316C",
        "Deep_Purple": "#473064",
        "Forest_Green": "#24352D",
        "J._Navy": "#333649",
        "Kelly": "#0D8F5F",
        "Maroon": "#5B1D32",
        "Neon_Green": "#C9FBA4",
        "Neon_Pink": "#FF76A2",
        "Royal": "#0D50A9",
        "Safety_Green": "#CCFF62",
        "Scuba_Blue": "#55D0D5",
        "True_Red": "#AF1632",
        "Vintage_Heather_Blue": "#63769E",
        "Vintage_Heather_Navy": "#515463",
        "Vintage_Heather_Red": "#AD535C",
        "White": "#EEEEE2",

        # Augusta Sportswear Tank Top Colors (703)
        "Black": "#252525",
        "Columbia_Blue": "#639CD3",
        "Gold": "#FDB417",
        "Graphite": "#73737B",
        "Kelly": "#028654",
        "Lime": "#BFD630",
        "Navy": "#023054",
        "Orange": "#E25623",
        "Power_Blue": "#0195DB",
        "Power_Yellow": "#FCEB05",
        "Purple": "#433584",
        "Red": "#CA1D39",
        "Royal": "#025797",
        "Silver_Grey": "#CECABE",
        "White": "#E3E3E3",

        # Badger Shorts Colors (7207)
        "Black": "#151517",
        "Brown": "#26211E",
        "Burnt_Orange": "#9F3211",
        "Cardinal": "#4B111D",
        "Columbia_Blue": "#557BAC",
        "Forest": "#232E2A",
        "Gold": "#B27502",
        "Graphite": "#2A2A2C",
        "Kelly": "#124323",
        "Maroon": "#230C14",
        "Navy": "#232531",
        "Purple": "#2D224C",
        "Red": "#9D0117",
        "Royal": "#17265D",
        "Silver": "#908C8B",
        "Vegas_Gold": "#8D7C50",
        "White": "#B1AFB2",
        
        # Basic color families (fallbacks)
        "blue": "#0000FF",
        "green": "#008000",
        "yellow": "#FFFF00",
        "orange": "#FFA500",
        "red": "#FF0000",
        "purple": "#800080",
        "grey": "#808080",
        "gray": "#808080",
        "brown": "#A52A2A",
        "pink": "#FFC0CB"


    }
    
    def __init__(self, claude_client=None):
        self.categories = {}
        self.product_data = {}
        self.claude_client = claude_client
        
        # Cache for product selection to avoid repeated API calls
        self.selection_cache = {}
        
        # Initialize product data
        self.init_product_data()
        
    def parse_sonar_analysis(self, analysis_text: str) -> Dict:
        """Parse the structured output from Claude's analysis"""
        preferences = {}
        patterns = {
            'category': r'Category:\s*([^\n]+)',
            'color': r'Color:\s*([^\n]+)',
            'material': r'Material:\s*([^\n]+)',
            'brand': r'Brand:\s*([^\n]+)',
            'price': r'Price Point:\s*([^\n]+)',
            'fit': r'Fit:\s*([^\n]+)',
            'size': r'Size:\s*([^\n]+)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, analysis_text)
            if match:
                value = match.group(1).strip()
                if value.lower() != "none":
                    preferences[key] = value
        logger.info(f"Parsed preferences (excluding None values): {preferences}")
        return preferences
    
    def map_category_to_internal(self, category: str) -> str:
        """Map Claude's category to our internal category names"""
        category = category.lower()
        category_map = {
            't-shirt': 't-shirt',
            'sweatshirt': 'hoodie',
            'long sleeve shirt': 'long-sleeve',
            'crewneck': 'crewneck',
            'sweatpants': 'sweatpants',
            'polo' :'polo',
            'tank top' : 'tank-top',
            'shorts' : 'shorts'
        }
        for key, value in category_map.items():
            if key in category:
                return value
        logger.warning(f"Could not map category '{category}' to internal category, defaulting to t-shirt")
        return 't-shirt'
    
    def get_color_hex(self, color_name: str) -> str:
        """Get hex code for a color name."""
        logger.info(f"get_color_hex called for '{color_name}'")
    
    # Step 1: Check if color_name is directly in the map
        if color_name in self.COLOR_HEX_MAP:
            logger.info(f"Exact match found for '{color_name}': {self.COLOR_HEX_MAP[color_name]}")
            return self.COLOR_HEX_MAP[color_name]
    
    # Step 2: Try with underscores instead of spaces
        color_with_underscores = color_name.replace(" ", "_")
        if color_with_underscores in self.COLOR_HEX_MAP:
            logger.info(f"Match found for '{color_with_underscores}': {self.COLOR_HEX_MAP[color_with_underscores]}")
            return self.COLOR_HEX_MAP[color_with_underscores]
    
    # Step 3: Try with spaces instead of underscores
        color_with_spaces = color_name.replace("_", " ")
        if color_with_spaces in self.COLOR_HEX_MAP:
            logger.info(f"Match found for '{color_with_spaces}': {self.COLOR_HEX_MAP[color_with_spaces]}")
            return self.COLOR_HEX_MAP[color_with_spaces]
    
    # Step 4: Case-insensitive comparison
        color_lower = color_name.lower()
        for key, hex_code in self.COLOR_HEX_MAP.items():
            if key.lower() == color_lower:
                logger.info(f"Case-insensitive match found: '{key}': {hex_code}")
                return hex_code
    
    # Step 5: Check if color_name is a substring of any key or vice versa
        for key, hex_code in self.COLOR_HEX_MAP.items():
            if color_lower in key.lower() or key.lower() in color_lower:
                logger.info(f"Substring match found: '{key}': {hex_code}")
                return hex_code
    
    # If not found in the dictionary, ask Claude
        logger.info(f"No matching color found in dictionary for '{color_name}', using Claude")
        return self.get_color_hex_with_claude(color_name)
    
    def get_color_hex_with_claude(self, color_name: str) -> str:
        """Get hex code for a color name using Claude for complex colors not in the dictionary."""
    # Create a cache key for this color if not already present
        cache_key = color_name.lower().strip()
    
        logger.info(f"get_color_hex_with_claude called for '{color_name}'")
    
    # Check if we've already generated this color before
        if hasattr(self, 'color_cache') and cache_key in self.color_cache:
            logger.info(f"Using cached hex code for '{color_name}': {self.color_cache[cache_key]}")
            return self.color_cache[cache_key]
    
    # Initialize cache if it doesn't exist
        if not hasattr(self, 'color_cache'):
            logger.info("Initializing color cache")
            self.color_cache = {}
    
    # Make sure we have a Claude client
        if not self.claude_client:
            logger.warning("No Claude client available for color conversion")
            return self.COLOR_HEX_MAP.get("red", "#FF0000")  # Default to red if no Claude
    
        try:
        # Prepare the prompt for Claude
            prompt = [
            {"role": "system", "content": """
                You are a color expert. Your task is to convert color descriptions into precise hex color codes.
                Respond ONLY with the hex code, nothing else.
                For compound colors like "red-orange", generate the appropriate blend.
                For "blend" in color names, interpret this as a gentle mixing of the colors mentioned.
                Format all responses as valid hexadecimal color codes (e.g., "#FF5500").
            """},
            {"role": "user", "content": f"Convert this color description to a hex code: {color_name}"}
        ]
        
        # Call Claude API
            logger.info(f"Asking Claude for hex code for complex color: '{color_name}'")
            response = self.claude_client.call_api(prompt, temperature=0.1)
            logger.info(f"Raw Claude response for '{color_name}': '{response}'")
        
        # Clean up and validate the response
            hex_code = response.strip()
        # Ensure it matches hex code format
            if re.match(r'^#[0-9A-Fa-f]{6}$', hex_code):
                logger.info(f"Claude generated hex code {hex_code} for '{color_name}'")
            
            # Cache the result for future use
                self.color_cache[cache_key] = hex_code
                return hex_code
            else:
            # Try to extract a hex code if Claude included other text
                match = re.search(r'#[0-9A-Fa-f]{6}', hex_code)
                if match:
                    hex_code = match.group(0)
                    logger.info(f"Extracted hex code {hex_code} from Claude response for '{color_name}'")
                    self.color_cache[cache_key] = hex_code
                    return hex_code
            
                logger.warning(f"Claude returned invalid hex code format: '{hex_code}'")
        except Exception as e:
            logger.error(f"Error getting hex code from Claude: {str(e)}", exc_info=True)
    
    # Fallback to the default color if Claude fails
        logger.warning(f"Falling back to default color for '{color_name}'")
        return self.COLOR_HEX_MAP.get("red", "#FF0000")
    
    # -------------------------------------------------------------------------
    # Enhanced get_closest_products_by_color using semantic mapping,
    # color family filtering, and perceptual HSL matching
    # -------------------------------------------------------------------------
    def get_closest_products_by_color(self, category: str, color_query: str, candidate_pool=None, max_products: int = 10) -> List[Dict]:
        """Find products with colors closest to the requested color, using semantic matching and perceptual distance."""
        logger.info(f"======== COLOR MATCHING PROCESS START ========")
        logger.info(f"Finding products for color query: '{color_query}' in category '{category}'")
        logger.info(f"Candidate pool size: {len(candidate_pool) if candidate_pool is not None else 'None'}")

        products = candidate_pool if candidate_pool is not None else self.categories[category].products
        if not products:
            logger.warning(f"No products found in category '{category}' or candidate pool")
            return []

        color_query_lower = color_query.lower()
        color_query_terms = color_query_lower.split()
        logger.info(f"Normalized color query: '{color_query_lower}'")
        logger.info(f"Color query terms: {color_query_terms}")

    # STEP 1: Check for exact color matches
        logger.info(f"STEP 1: Checking for exact color name matches")
        exact_matches = []
        for product in products:
            product_color_lower = product['color'].lower()
            if color_query_lower == product_color_lower:
                logger.info(f"  Exact match found: {product['product_name']} in {product['color']}")
                exact_matches.append(product)

        if exact_matches:
            logger.info(f"Found {len(exact_matches)} exact color matches for '{color_query}'")
            logger.info(f"======== COLOR MATCHING COMPLETE: EXACT MATCHES ========")
            return exact_matches[:max_products]
        else:
            logger.info(f"No exact color matches found for '{color_query}'")

    # STEP 2: Check for semantic color matching
        logger.info(f"STEP 2: Checking for semantic color matching")
        semantic_matches = []
        direct_matches = []  # For when color query directly matches a semantic term

    # First, check if color query directly matches any semantic term
        logger.info(f"  Checking for direct matches with semantic terms")
        for semantic_term, color_list in SEMANTIC_COLOR_MAP.items():
            if semantic_term == color_query_lower:
                logger.info(f"  Direct semantic term match found: '{semantic_term}'")
                for product in products:
                    product_color = product['color'].lower()
                    for color in color_list:
                        if color.lower() == product_color:
                            logger.info(f"    Adding product: {product['product_name']} in {product['color']}")
                            direct_matches.append(product)

        if direct_matches:
            logger.info(f"Found {len(direct_matches)} direct semantic term matches for '{color_query}'")
            logger.info(f"======== COLOR MATCHING COMPLETE: DIRECT SEMANTIC MATCHES ========")
            return direct_matches[:max_products]
        else:
            logger.info(f"No direct semantic term matches found for '{color_query}'")

    # Next, look for semantic matches with proper containment checks
        logger.info(f"  Checking for partial semantic term matches")
        for semantic_term, color_list in SEMANTIC_COLOR_MAP.items():
        # Check if the query is in this semantic category
            semantic_match = False
            match_reason = ""
    
            if semantic_term == color_query_lower:
                semantic_match = True
                match_reason = "exact term match"
            elif semantic_term in color_query_lower.split():
                semantic_match = True
                match_reason = f"'{semantic_term}' is a word in the query"
            elif color_query_lower in semantic_term.split():
                semantic_match = True
                match_reason = f"query is a word in '{semantic_term}'"
    
            if semantic_match:
                logger.info(f"  Semantic category match: '{semantic_term}' - {match_reason}")
                for product in products:
                    product_color = product['color'].lower()
                    for color in color_list:
                        color_lower = color.lower()
                        if (color_lower == product_color or 
                            color_lower in product_color.split() or 
                            product_color in color_lower.split()):
                            # Check if this product is already in semantic_matches
                            is_duplicate = any(p.get('product_name') == product.get('product_name') and 
                                    p.get('color') == product.get('color') for p in semantic_matches)
                            if not is_duplicate:
                                logger.info(f"    Adding product: {product['product_name']} in {product['color']}")
                                semantic_matches.append(product)
                            else:
                                logger.info(f"    Skipping duplicate: {product['product_name']} in {product['color']}")

    # STEP 3: Color Family Filtering
        logger.info(f"STEP 3: Checking for color family matches")
        base_color = color_query_terms[-1] if len(color_query_terms) > 0 else ""
        modifiers = color_query_terms[:-1] if len(color_query_terms) > 1 else []

        logger.info(f"  Base color term identified: '{base_color}'")
        logger.info(f"  Modifiers identified: {modifiers}")

    # Find the most specific color family match
        target_family = None
        family_match_reason = ""

        for family in COLOR_FAMILIES:
            if family == base_color:  # Exact family match
                target_family = family
                family_match_reason = f"exact match with '{family}'"
                logger.info(f"  Color family match: {family} - {family_match_reason}")
                break
            elif family in base_color or base_color in family:
            # Store potential match but keep looking for exact
                if target_family is None:
                    target_family = family
                    family_match_reason = f"partial match between '{family}' and '{base_color}'"
                    logger.info(f"  Potential color family match: {family} - {family_match_reason}")

        if target_family:
            logger.info(f"  Target color family selected: '{target_family}' - {family_match_reason}")
            family_filtered = []
    
            for product in products:
                product_color_hex = self.get_color_hex(product['color'])
                product_family = determine_color_family(product_color_hex)
                logger.info(f"  Product: {product['product_name']} in {product['color']} - Family: {product_family}, Hex: {product_color_hex}")
        
                if product_family == target_family:
                    logger.info(f"    Color family match - adding to filtered list")
                    family_filtered.append(product)
                else:
                    logger.info(f"    Not in target family '{target_family}' - skipping")
    
            if family_filtered:
                logger.info(f"Filtered to {len(family_filtered)} products in the '{target_family}' color family")
                products = family_filtered
            else:
                logger.info(f"No products found in the '{target_family}' color family")
        else:
            logger.info(f"No matching color family found for '{base_color}'")

    # STEP 4: HSL Perceptual Distance Matching with Enhanced Prioritization
        logger.info(f"STEP 4: Performing HSL perceptual distance matching with enhanced prioritization")

    # Use get_color_hex for the target color rather than using the base color
        target_hex = self.get_color_hex(color_query)
        logger.info(f"  CRITICAL: Target hex code for full color query '{color_query}': {target_hex}")

        target_hsl = hex_to_hsl(target_hex)
        logger.info(f"  Target HSL for '{color_query}': H={target_hsl[0]} (hue), S={target_hsl[1]:.2f}% (saturation), L={target_hsl[2]:.2f}% (lightness)")

    # Log color wheel position for context
        hue_position = ""
        if 0 <= target_hsl[0] < 30:
            hue_position = "red/red-orange range"
        elif 30 <= target_hsl[0] < 60:
            hue_position = "orange/yellow-orange range"
        elif 60 <= target_hsl[0] < 90:
            hue_position = "yellow range"
        elif 90 <= target_hsl[0] < 150:
            hue_position = "green range"
        elif 150 <= target_hsl[0] < 210:
            hue_position = "cyan/teal range"
        elif 210 <= target_hsl[0] < 270:
            hue_position = "blue range"
        elif 270 <= target_hsl[0] < 330:
            hue_position = "purple/magenta range"
        else:
            hue_position = "pink/red range"

        logger.info(f"  Target color hue {target_hsl[0]} is in the {hue_position}")

    # NEW: Enhanced prioritization logic based on term matching
    # Create priority groups for products
        exact_compound_matches = []  # 1. Exact compound term matches
        multiple_word_matches = []   # 2. Multiple word matches
        single_word_matches = []     # 3. Single word matches
        no_word_matches = []         # 4. No word matches (perceptual only)

        logger.info(f"  Categorizing products by new prioritization logic:")

        for product in products:
            product_color = product['color']
            product_color_lower = product_color.lower()
            product_color_terms = product_color_lower.split()
            product_hex = self.get_color_hex(product_color)
            product_hsl = hex_to_hsl(product_hex)
        
        # Calculate HSL distance for each product
            distance = hsl_distance(target_hsl, product_hsl)
        
            logger.info(f"  Product: '{product_color}' - Hex: {product_hex}, HSL: H={product_hsl[0]}, S={product_hsl[1]:.2f}, L={product_hsl[2]:.2f}")
            logger.info(f"    Base HSL distance: {distance:.4f}")
        
        # Apply modifier adjustments
            original_distance = distance
            modifier_applied = False

        for modifier in modifiers:
            if modifier == "light" and product_hsl[2] < 50:
                distance *= 1.8  # Increased penalty
                logger.info(f"    Applied 'light' modifier penalty: {original_distance:.4f} → {distance:.4f}")
                modifier_applied = True
            elif modifier == "dark" and product_hsl[2] > 50:
                distance *= 1.8  # Increased penalty
                logger.info(f"    Applied 'dark' modifier penalty: {original_distance:.4f} → {distance:.4f}")
                modifier_applied = True
            elif modifier == "bright" and product_hsl[1] < 60:
                distance *= 1.8  # Increased penalty
                logger.info(f"    Applied 'bright' modifier penalty: {original_distance:.4f} → {distance:.4f}")
                modifier_applied = True

# Add special handling for "vintage" modifier
                if "vintage" in color_query_lower and "vintage" in product_color_lower:
    # Apply a 30% bonus (multiply distance by 0.7) for products with "vintage" in their name
                    distance *= 0.7
                    logger.info(f"    Applied 'vintage' bonus: {original_distance:.4f} → {distance:.4f}")
                    modifier_applied = True

            if not modifier_applied and modifiers:
                logger.info(f"    No modifier penalties applied for {modifiers}")
        
        # NEW: Determine which priority group this product belongs to
            if color_query_lower == product_color_lower:
            # This should have been caught earlier, but just in case
                logger.info(f"    Priority: Exact compound match (highest)")
                exact_compound_matches.append((distance, product))
            elif len(color_query_terms) > 1 and all(term in product_color_lower for term in color_query_terms):
            # All query terms exist in the product color (in any order)
                logger.info(f"    Priority: Multiple word match - all terms present")
                exact_compound_matches.append((distance, product))
            elif len(color_query_terms) > 1:
            # Check how many query terms match
                matching_terms = [term for term in color_query_terms if term in product_color_terms]
                if len(matching_terms) > 1:
                    logger.info(f"    Priority: Multiple word match - {len(matching_terms)} terms match: {matching_terms}")
                    multiple_word_matches.append((distance, product, len(matching_terms)))
                elif len(matching_terms) == 1:
                    logger.info(f"    Priority: Single word match - term: {matching_terms[0]}")
                    single_word_matches.append((distance, product, matching_terms[0]))
                else:
                # No direct term matches, check for substring matches
                    if any(term in product_color_lower for term in color_query_terms) or any(term in color_query_lower for term in product_color_terms):
                        logger.info(f"    Priority: Substring match")
                        single_word_matches.append((distance * 1.2, product, "substring"))  # Slight penalty for substring vs. word
                    else:
                        logger.info(f"    Priority: No word match - using perceptual distance only")
                        no_word_matches.append((distance, product))
            else:
            # Single term query, check if it matches any terms in product color
                if color_query_lower in product_color_terms:
                    logger.info(f"    Priority: Single word exact match")
                    single_word_matches.append((distance, product, "exact"))
                elif color_query_lower in product_color_lower:
                    logger.info(f"    Priority: Single word substring match")
                    single_word_matches.append((distance * 1.2, product, "substring"))  # Slight penalty
                else:
                    logger.info(f"    Priority: No word match - using perceptual distance only")
                    no_word_matches.append((distance, product))
    
    # Sort each priority group internally
        exact_compound_matches.sort(key=lambda x: x[0])
        multiple_word_matches.sort(key=lambda x: (x[2] * -1, x[0]))  # More matching words first, then by distance
        single_word_matches.sort(key=lambda x: x[0])  # By distance
        no_word_matches.sort(key=lambda x: x[0])  # By distance
    
    # Combine results in priority order
        results = []
    
    # Add products from each group in order of priority
        results.extend([product for _, product in exact_compound_matches])
        results.extend([product for _, product, _ in multiple_word_matches])
        results.extend([product for _, product, _ in single_word_matches])
        results.extend([product for _, product in no_word_matches])
    
    # Log the final prioritized results
        logger.info(f"Final prioritized color matches for '{color_query}':")
        for i, product in enumerate(results[:5]):
            logger.info(f"  {i+1}. {product['product_name']} in {product['color']}")
    
        logger.info(f"Found {len(results)} products for color '{color_query}', returning top {max_products}")
        logger.info(f"======== COLOR MATCHING PROCESS COMPLETE ========")
    
        return results[:max_products]
    
    def select_product_with_claude(self, category: str, user_query: str, preferences: Dict) -> Tuple[Optional[Dict], str]:
        """Use Claude to select the best product from a category based on preferences."""
        if category not in self.categories:
            logger.warning(f"Category {category} not found, defaulting to t-shirt")
            category = 't-shirt'
        products = self.categories[category].products
        filtered_products = []
        if 'color' in preferences:
            color_name = preferences['color']
            filtered_products = self.get_closest_products_by_color(category, color_name)
            logger.info(f"Pre-filtered to {len(filtered_products)} products based on color proximity to {color_name}")
        if filtered_products:
            products = filtered_products
        if len(products) > 10:
            logger.info(f"Limiting from {len(products)} to 10 products for API efficiency")
            products = products[:10]
        product_options = []
        for product in products:
            material_type = "100% Cotton" if "100% Cotton" in product['material'].lower() else \
                           "Athletic/Polyester" if "polyester" in product['material'].lower() else \
                           "Cotton/Poly Blend"
            product_options.append(
                f"Product: {product['product_name']}\n"
                f"Color: {product['color']}\n"
                f"Material: {product['material']} (Type: {material_type})\n"
                f"Brand: {product['product_name'].split(' ')[0]}\n"
                f"Price: {product['price']}\n"
            )
        product_list = "\n---\n".join(product_options)
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
        preferences_text = "\n".join([f"{k.capitalize()}: {v}" for k, v in preferences.items()])
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
        try:
            response = self.claude_client.call_api(prompt, temperature=0.1)
            match = re.search(r"SELECTED: (.+) in (.+)$", response, re.MULTILINE)
            if match:
                product_name = match.group(1).strip()
                color = match.group(2).strip()
                logger.info(f"Claude's raw selection: SELECTED: {product_name} in {color}")
                logger.info(f"Claude's response excerpt: {response[-200:]}")
                for idx, product in enumerate(products[:5]):
                    logger.info(f"Product {idx}: '{product['product_name']}' in '{product['color']}'")
                for product in products:
                    product_name_norm = re.sub(r'[^\w\s]', '', product['product_name']).lower().strip()
                    product_color_norm = re.sub(r'[^\w\s]', '', product['color']).lower().strip()
                    match_name_norm = re.sub(r'[^\w\s]', '', product_name).lower().strip()
                    match_color_norm = re.sub(r'[^\w\s]', '', color).lower().strip()
                    if product_name_norm == match_name_norm and product_color_norm == match_color_norm:
                        return product, response
                    elif match_name_norm in product_name_norm and match_color_norm in product_color_norm:
                        return product, response
                logger.warning(f"Could not find exact product match for '{product_name}' in '{color}'")
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
                        logger.info(f"Fallback to color match: {color_matches[0]['product_name']} in {color_matches[0]['color']}")
                        return color_matches[0], "Fallback to color match: No exact product match found, but matched requested color."
            else:
                logger.warning(f"Could not parse product selection from Claude's response")
        except Exception as e:
            logger.error(f"Error in Claude product selection: {str(e)}")
            response = f"Error: {str(e)}"
        if products:
            if 'color' in preferences:
                requested_color = preferences['color'].lower()
                for product in products:
                    if requested_color in product['color'].lower():
                        logger.warning(f"Fallback to color match: {product['product_name']} in {product['color']}")
                        return product, "Fallback to color match"
            if 'material' in preferences:
                requested_material = preferences['material'].lower()
                for product in products:
                    if requested_material in product['material'].lower():
                        logger.warning(f"Fallback to material match: {product['product_name']} with {product['material']}")
                        return product, "Fallback to material match"
            logger.warning(f"Fallback to first product in category: {products[0]['product_name']}")
            return products[0], "Fallback to first product in category"
        return None, response
    
    def select_product(self, query: str, sonar_analysis: str, rejected_products=None) -> Optional[Dict]:
        """
        Select a product based on user query and Claude's analysis using a deduction system.
        Filter products by hard constraints rather than using scores.
        """
        try:
        # Start with comprehensive logging of input
            logger.info(f"=== PRODUCT SELECTION STARTED ===")
            logger.info(f"Query: '{query}'")
            logger.info(f"Sonar Analysis: '{sonar_analysis}'")
        
        # Parse preferences
            preferences = self.parse_sonar_analysis(sonar_analysis)
            logger.info(f"Preferences extracted: {preferences}")
            logger.info(f"Color preference: {preferences.get('color', 'None')}")
            logger.info(f"Material preference: {preferences.get('material', 'None')}")

            if 'color' not in preferences and hasattr(self, 'original_intent_context'):
                if self.original_intent_context.get('general_color'):
                    original_color = self.original_intent_context.get('general_color')
                    logger.info(f"Missing color in query - adding original color '{original_color}' from intent")
                    preferences['color'] = original_color
        
        # Get category
            original_category = None
            if 'category' in preferences:
                original_category = preferences['category']
                category = self.map_category_to_internal(preferences['category'])
            else:
                category = 't-shirt'
                original_category = "T-Shirt"
            logger.info(f"Category identified: {category} (original: {original_category})")
        
        # Validate category
            if category not in self.categories:
                logger.warning(f"Category '{category}' not found in available categories. Defaulting to 't-shirt'")
                category = 't-shirt'
        
        # Get all products in the category
            all_category_products = self.categories[category].products
            logger.info(f"Starting with {len(all_category_products)} products in category: {category}")
        
        # Step 1: Initialize candidate pool
            candidate_products = all_category_products.copy()
        
        # Step 2: Remove rejected products
            if rejected_products:
                before_count = len(candidate_products)
                candidate_products = [
                    product for product in candidate_products 
                    if not any(
                        product.get('product_name') == rejected.get('product_name') and 
                        product.get('color') == rejected.get('color')
                        for rejected in rejected_products
                    )
                ]
                logger.info(f"Rejected products filter: {before_count} → {len(candidate_products)} products")
        
        # Step 3: Filter by material
            if 'material' in preferences:
                requested_material = preferences['material'].lower()
                logger.info(f"Filtering by material: '{requested_material}'")
            
                before_count = len(candidate_products)
            
            # Material filter logic with case-insensitive comparison - fixed the case sensitivity issue!
                if "100% cotton" in requested_material.lower():
                    logger.info("Looking for 100% cotton products with case-insensitive match")
                    candidate_products = [p for p in candidate_products if "100% cotton".lower() in p['material'].lower()]
                elif "polyester" in requested_material:
                    candidate_products = [p for p in candidate_products if "polyester" in p['material'].lower()]
                elif "blend" in requested_material or "cotton/poly" in requested_material:
                    candidate_products = [p for p in candidate_products if 
                                    ("blend" in p['material'].lower() or "/50" in p['material'].lower() or 
                                     ("cotton" in p['material'].lower() and "poly" in p['material'].lower()))]
                else:
                    candidate_products = [p for p in candidate_products if requested_material in p['material'].lower()]
            
                logger.info(f"Material filter: {before_count} → {len(candidate_products)} products")
            
            # Log first few products that passed material filter
                for idx, p in enumerate(candidate_products[:3]):
                    logger.info(f"  After material filter product {idx}: {p.get('product_name')} in {p.get('color')} with material '{p.get('material')}'")
            
            # Material fallback if no matches
                if not candidate_products:
                    logger.warning(f"No products match the material requirement: {preferences['material']}. Continuing with all products in category.")
                    candidate_products = all_category_products.copy()
        
        # Step 4: Filter by brand
            if 'brand' in preferences and candidate_products:
                requested_brand = preferences['brand'].lower()
                logger.info(f"Filtering by brand: '{requested_brand}'")
            
                before_count = len(candidate_products)
                brand_matched_products = []
            
                for product in candidate_products:
                    product_brand = product['product_name'].split(' ')[0].lower()
                    if requested_brand in product_brand or product_brand in requested_brand:
                        brand_matched_products.append(product)
            
                if brand_matched_products:
                    candidate_products = brand_matched_products
                    logger.info(f"Brand filter: {before_count} → {len(candidate_products)} products")
            
            color_filtered_copy = None
        
        # Step 5: Filter by color - CRITICAL PART
            if 'color' in preferences and candidate_products:
                color_name = preferences['color']
                logger.info(f"Filtering by color: '{color_name}'")
            
                before_count = len(candidate_products)
            
            # Get color-filtered products
                color_filtered_products = self.get_closest_products_by_color(
                    category, color_name, 
                    candidate_pool=candidate_products,
                    max_products=10
                )
            
            # Log extensive details about color filtering
                logger.info(f"get_closest_products_by_color returned {len(color_filtered_products) if color_filtered_products else 0} products")
            
                if color_filtered_products:
                    logger.info("Color-filtered products (showing up to 5):")
                    for idx, product in enumerate(color_filtered_products[:5]):
                        logger.info(f"  Color-filtered product {idx}: {product.get('product_name')} in {product.get('color')}")
                
                # CREATE A CHECKPOINT COPY before assignment to detect later changes
                    color_filtered_copy = color_filtered_products.copy()
                    logger.info(f"Created checkpoint copy with {len(color_filtered_copy)} products")
                
                # CRITICAL LINE: Update the candidate pool
                    candidate_products = color_filtered_products
                    logger.info(f"Color filter: {before_count} → {len(candidate_products)} products")
                
                # Verify assignment worked correctly
                    if id(candidate_products) == id(color_filtered_products):
                        logger.info("Assignment verified: candidate_products and color_filtered_products have same id")
                    else:
                        logger.warning("Assignment issue: candidate_products and color_filtered_products have different id")
                else:
                    logger.warning(f"No products match the color '{color_name}' after filtering")
        
        # Step 6: Check candidate pool state after all filters
            logger.info(f"Candidate pool after all filters: {len(candidate_products)} products")
            if candidate_products:
                logger.info("Candidates after all filters (showing up to 3):")
                for idx, product in enumerate(candidate_products[:3]):
                    logger.info(f"  Final candidate {idx}: {product.get('product_name')} in {product.get('color')} with material '{product.get('material')}'")
            
            # If we had color filtering, verify candidates still match color
                if 'color' in preferences and color_filtered_copy:
                # Check if any of the color-filtered products are still in the candidate pool
                    overlap = [p for p in candidate_products if any(
                        p.get('product_name') == cp.get('product_name') and p.get('color') == cp.get('color')
                        for cp in color_filtered_copy
                    )]
                
                    logger.info(f"Color filter integrity check: {len(overlap)}/{len(candidate_products)} candidates were in the original color-filtered set")
                
                    if len(overlap) < len(candidate_products):
                        logger.error("COLOR FILTER INTEGRITY FAILURE: Some products in the candidate pool weren't in the color-filtered set!")
                        for p in candidate_products:
                            if p not in overlap:
                                logger.error(f"  Non-matching product: {p.get('product_name')} in {p.get('color')}")
            else:
                logger.warning("No products remain after applying all filters")
                return None
        
        # Step 7: Apply price sorting if requested
            if 'price' in preferences:
                requested_price = preferences['price'].lower()
                before_count = len(candidate_products)
                if "affordable" in requested_price or "cheaper" in requested_price or "less expensive" in requested_price:
                    logger.info(f"Sorted by price (ascending) for affordable preference")
                    candidate_products.sort(key=lambda p: float(p['price'].replace('$', '').strip()))
                    candidate_products = candidate_products[:3] # Take the 3 cheapest
                    logger.info(f"Price filter: {before_count} → {len(candidate_products)} products")
                elif "premium" in requested_price or "expensive" in requested_price or "higher quality" in requested_price:
                    logger.info(f"Sorted by price (descending) for premium preference")
                    candidate_products.sort(key=lambda p: float(p['price'].replace('$', '').strip()), reverse=True)
                    candidate_products = candidate_products[:3] # Take the 3 most expensive
                    logger.info(f"Price filter: {before_count} → {len(candidate_products)} products")

        
        # Step 8: Handle cheaper request if applicable
            is_cheaper_request = "cheaper" in query.lower() or "less expensive" in query.lower()
            if is_cheaper_request and rejected_products and len(rejected_products) > 0:
                latest_rejected = rejected_products[-1]
                logger.info(f"Processing cheaper request relative to: {latest_rejected.get('product_name')} in {latest_rejected.get('color')} at {latest_rejected.get('price')}")
            
                try:
                    comparison_price = float(latest_rejected.get('price', '').replace('$', ''))
                    before_count = len(candidate_products)
                
                    cheaper_products = [
                        p for p in candidate_products 
                        if float(p['price'].replace('$', '').strip()) < comparison_price
                    ]
                
                    if cheaper_products:
                        candidate_products = cheaper_products
                        candidate_products.sort(key=lambda p: float(p['price'].replace('$', '').strip()))
                        logger.info(f"Cheaper filter: {before_count} → {len(candidate_products)} products")
                    else:
                        logger.info(f"No cheaper products found below ${comparison_price}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse price for comparison: {e}")
        
        # FINAL STEP: Select the best match
            if candidate_products:
            # ADDITIONAL CHECK: For color preference, ensure top candidate has right color
                if 'color' in preferences and len(candidate_products) > 1:
                    color_name = preferences['color'].lower()
                
                # Look for better color match among top candidates
                    color_candidates = []
                    for product in candidate_products[:5]:  # Check top 5
                        product_color = product.get('color', '').lower()
                        if color_name in product_color or product_color in color_name:
                            logger.info(f"Found direct color match: {product.get('product_name')} in {product.get('color')}")
                            color_candidates.append(product)
                
                # If we found better color matches, prioritize them
                    if color_candidates:
                        logger.info(f"Found {len(color_candidates)} products with direct color name matches")
                        candidate_products = color_candidates + [p for p in candidate_products if p not in color_candidates]
            
            # Select first candidate after all filtering and prioritization
                selected_product = candidate_products[0]
                logger.info(f"FINAL SELECTION: {selected_product['product_name']} in {selected_product['color']} at {selected_product['price']}")
            
            # If color preference exists, validate the selection
                if 'color' in preferences:
                    color_name = preferences['color'].lower()
                    selected_color = selected_product.get('color', '').lower()
                
                    color_match = color_name in selected_color or selected_color in color_name
                    logger.info(f"Color preference validation: '{color_name}' vs '{selected_color}' - Match: {color_match}")
                
                    if not color_match:
                        logger.warning(f"SELECTED COLOR MISMATCH: Requested '{color_name}' but selected '{selected_color}'")
                    
                        # Try one more time to find a better color match
                        for product in candidate_products[1:5]:  # Try next few products
                            p_color = product.get('color', '').lower()
                            if color_name in p_color or p_color in color_name:
                                logger.info(f"Found better color match: {product.get('product_name')} in {product.get('color')}")
                                selected_product = product
                            logger.info(f"REVISED SELECTION: {selected_product['product_name']} in {selected_product['color']}")
                            break
            
            # Add category and return
                selected_product['category'] = original_category
                return selected_product  # Add this line!
        
            # No products matched - fallback
            logger.warning("No product matched all criteria, falling back to default")
            if 't-shirt' in self.categories and self.categories['t-shirt'].products:
                default_product = self.categories['t-shirt'].products[0].copy()
                default_product['category'] = original_category or "T-Shirt"
                logger.info(f"FALLBACK SELECTION: {default_product.get('product_name')} in {default_product.get('color')}")
                logger.info("=== PRODUCT SELECTION COMPLETED WITH FALLBACK ===")
                return default_product
        
            logger.error("No products available even for fallback")
            logger.info("=== PRODUCT SELECTION FAILED ===")
            return None
        
        except Exception as e:
            logger.error(f"Error in product selection: {str(e)}", exc_info=True)
        
        # Emergency fallback
        if self.categories.get('t-shirt') and self.categories['t-shirt'].products:
            default_product = self.categories['t-shirt'].products[0].copy()
            default_product['category'] = "T-Shirt"
            logger.info(f"ERROR FALLBACK SELECTION: {default_product.get('product_name')} in {default_product.get('color')}")
            logger.info("=== PRODUCT SELECTION COMPLETED WITH ERROR FALLBACK ===")
            return default_product
        
        logger.error("No products available even for error fallback")
        logger.info("=== PRODUCT SELECTION FAILED WITH ERROR ===")
        return None
    
    def get_product_by_style_color(self, style: str, color: str) -> Optional[Dict]:
        """Get product by style number and color"""
        key = f"{style}_{color}"
        return self.product_data.get(key)
    
    def set_original_intent_context(self, intent):
        """Store original intent for context during selection"""
        self.original_intent_context = intent
        logger.info(f"Set original intent context: {intent}")
    
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
                'material': 'Cotton/Poly Blend',
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
                'material': '100% Polyester',
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
            "Carolina_Blue", "Dark_Grey", "Dusty_Blue", "Forest", "Gold", "Kelly", 
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
                'material': '100% Cotton',
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
                'material': '100% Cotton',
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
                'material': '100% Cotton',
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
                'material': '100% Polyester',
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
                'material': 'Cotton/Poly Blend',
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
                'material': 'Cotton/Poly Blend',
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

        # Hoodies category - add JERZEES NuBlend Hoodie to existing hoodie category
        jerzees_hoodie_colors = [
            "Ash", "Athletic_Heather", "Black", "Black_Heather", "Burnt_Orange", 
            "Charcoal_Grey", "Cyber_Pink", "Deep_Purple", "Forest_Green", "J._Navy", 
            "Kelly", "Maroon", "Neon_Green", "Neon_Pink", "Royal", "Safety_Green", 
            "Scuba_Blue", "True_Red", "Vintage_Heather_Blue", "Vintage_Heather_Navy", 
            "Vintage_Heather_Red", "White"
        ]
        for color in jerzees_hoodie_colors:
            self.categories['hoodie'].add_product({
        'style_number': '996',
        'product_name': 'JERZEES - NuBlend Hooded Sweatshirt',
        'color': color.replace("_", " "),
        'price': '$21.99',
        'material': 'Cotton/Poly Blend',
        'weight': 'midweight',
        'fit': 'standard',
        'has_youth_sizes': True,
        'has_adult_sizes': True,
        'youth_sizes': 'S-XL',
        'adult_sizes': 'S-5XL',
        'features': [
            'NuBlend pill-resistant fleece',
            'High-stitch density for smooth printing',
            '2-ply hood with grommets and drawcord',
            'Pouch pocket',
            'Ribbed cuffs and waistband'
        ],
        'images': {
            'front': f'/productimages/996/JERZEES_996MR_{color}_Front_High.jpg',
            'back': f'/productimages/996/JERZEES_996MR_{color}_Back_High.jpg'
        }
        })

            # Tank Top category (new)
        self.categories['tank-top'] = ProductCategory('Tank Tops', claude_client=self.claude_client)
        augusta_tank_colors = [
            "Black", "Columbia_Blue", "Gold", "Graphite", "Kelly", "Lime", "Navy", 
            "Orange", "Power_Blue", "Power_Yellow", "Purple", "Red", "Royal", 
            "Silver_Grey", "White"
        ]
        for color in augusta_tank_colors:
            self.categories['tank-top'].add_product({
            'style_number': '703',
            'product_name': 'Augusta Sportswear - Wicking Tank Top',
        'color': color.replace("_", " "),
        'price': '$15.99',
        'material': '100% Polyester',
        'weight': 'lightweight',
        'fit': 'athletic',
        'has_youth_sizes': True,
        'has_adult_sizes': True,
        'youth_sizes': 'S-L',
        'adult_sizes': 'S-3XL',
        'features': [
            'Moisture-wicking performance fabric',
            'Self-fabric binding at neck and armholes',
            'Double-needle hemmed bottom',
            'Tear away label'
        ],
        'images': {
            'front': f'/productimages/703/Augusta_Sportswear_703_{color}_Front_High.jpg',
            'back': f'/productimages/703/Augusta_Sportswear_703_{color}_Back_High.jpg'
        }
        })

            # Shorts category (new)
        self.categories['shorts'] = ProductCategory('Shorts', claude_client=self.claude_client)
        badger_shorts_colors = [
            "Black", "Brown", "Burnt_Orange", "Cardinal", "Columbia_Blue", "Forest", 
            "Gold", "Graphite", "Kelly", "Maroon", "Navy", "Purple", "Red", "Royal", 
            "Silver", "Vegas_Gold", "White"
        ]
        for color in badger_shorts_colors:
            self.categories['shorts'].add_product({
        'style_number': '7207',
        'product_name': 'Badger - Mesh Athletic Shorts',
        'color': color.replace("_", " "),
        'price': '$16.99',
        'material': '100% Polyester',
        'weight': 'lightweight',
        'fit': 'athletic',
        'has_youth_sizes': True,
        'has_adult_sizes': True,
        'youth_sizes': 'S-L',
        'adult_sizes': 'S-3XL',
        'features': [
            '100% polyester mesh',
            'Polyester tricot liner',
            'Athletic cut for superior fit',
            'Covered elastic waistband with drawcord'
        ],
        'images': {
            'front': f'/productimages/7207/Badger_7207_{color}_Front_High.jpg',
            'back': f'/productimages/7207/Badger_7207_{color}_Back_High.jpg'
        }
        })    
        
        # Crewneck sweatshirts
        self.categories['crewneck'] = ProductCategory('Crewneck Sweatshirts', claude_client=self.claude_client)
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
                'material': 'Cotton/Poly Blend',
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
        jerzees_sweatpants_colors = [
            "Black", "Ash", "Forest_Green", "J._Navy", "Maroon", "Oxford", "Royal", "True_Red"
        ]
        for color in jerzees_sweatpants_colors:
            self.categories['sweatpants'].add_product({
                'style_number': '973M',
                'product_name': 'JERZEES - NuBlend Sweatpants',
                'color': color.replace("_", " "),
                'price': '$18.50',
                'material': 'Cotton/Poly Blend',
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

        # Polos category
        self.categories['polo'] = ProductCategory('Polos', claude_client=self.claude_client)

        # Gildan DryBlend Polo (8800)
        gildan_polo_colors = [
            "Black", "Gold", "Light_Blue", "Maroon", "Navy", 
            "Red", "Royal", "Sport_Grey", "White"
        ]
        for color in gildan_polo_colors:
            self.categories['polo'].add_product({
                'style_number': '8800',
                'product_name': 'Gildan - DryBlend Pique Polo',
                'color': color.replace("_", " "),
                'price': '$16.99',
                'material': 'Cotton/Poly Blend',
                'weight': 'midweight',
                'fit': 'classic',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'S-XL',
                'adult_sizes': 'S-5XL',
                'features': [
                'DryBlend moisture-wicking technology',
                'Three-button placket',
                'Contoured welt collar and cuffs',
                'Tear away label'
            ],
                'images': {
                'front': f'/productimages/8800/Gildan_8800_{color}_Front_High.jpg',
                'back': f'/productimages/8800/Gildan_8800_{color}_Back_High.jpg'
            }
        })


# AllPro Performance Polo (41800)
        allpro_polo_colors = [
            "Black", "Carolina_Blue", "Forest_Green", "Greystone", "Heather_Navy",
            "Heather_Steel", "Maroon", "Navy", "Pacific_Blue", "Red", "Royal", "White"
            ]
        for color in allpro_polo_colors:
            self.categories['polo'].add_product({
                'style_number': '41800',
                'product_name': 'AllPro - Performance Polo',
                'color': color.replace("_", " "),
                'price': '$17.99',
                'material': '100% Polyester',
                'weight': 'lightweight',
                'fit': 'standard',
                'has_youth_sizes': True,
                'has_adult_sizes': True,
                'youth_sizes': 'S-XL',
                'adult_sizes': 'S-3XL',
                'features': [
                    'Moisture-management properties',
                    'Snag resistant',
                    'Three-button placket',
                    'UPF rating of 50',
                    'Tear away label'
                ],
                'images': {
                    'front': f'/productimages/41800/AllPro_41800_{color}_Front_High.jpg',
                    'back': f'/productimages/41800/AllPro_41800_{color}_Back_High.jpg'
                }
            })

        # Map all products to make lookup easier by style number and color
        for category in self.categories.values():
            for product in category.products:
                style = product['style_number']
                color = product['color']
                key = f"{style}_{color}"
                self.product_data[key] = product