from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime

@dataclass
class OrderState:
    """Tracks the state of an order through the sales process"""
    # Product Selection
    product_selected: bool = False
    product_details: Optional[Dict] = None
    
    # Design Placement
    design_uploaded: bool = False
    design_path: Optional[str] = None
    placement_selected: bool = False
    placement: Optional[str] = None
    
    # Quantities
    quantities_collected: bool = False
    sizes: Optional[Dict[str, int]] = None
    total_quantity: int = 0
    total_price: float = 0
    
    # Customer Information
    customer_info_collected: bool = False
    customer_name: Optional[str] = None
    shipping_address: Optional[str] = None
    email: Optional[str] = None
    
    # Payment Information
    payment_url: Optional[str] = None

    def update_product(self, details: Dict):
        self.product_selected = True
        self.product_details = details
    
    def update_design(self, design_path: str, placement: str):
        self.design_uploaded = True
        self.design_path = design_path
        self.placement_selected = True
        self.placement = placement
    
    def update_quantities(self, sizes: Dict[str, int], price_per_item: float):
        self.quantities_collected = True
        self.sizes = sizes
        self.total_quantity = sum(sizes.values())
        self.total_price = self.total_quantity * price_per_item
    
    def update_customer_info(self, name: str, address: str, email: str):
        self.customer_info_collected = True
        self.customer_name = name
        self.shipping_address = address
        self.email = email
    
    def get_next_required_step(self) -> str:
        """Returns the next step needed to complete the order"""
        if not self.product_selected:
            return "product_selection"
        if not self.design_uploaded or not self.placement_selected:
            return "design_placement"
        if not self.quantities_collected:
            return "quantity_collection"
        if not self.customer_info_collected:
            return "customer_information"
        return "complete"
    
    def is_complete(self) -> bool:
        """Check if all required information has been collected"""
        return all([
            self.product_selected,
            self.design_uploaded,
            self.placement_selected,
            self.quantities_collected,
            self.customer_info_collected
        ])
    
    def to_dict(self) -> Dict:
        """Convert the order state to a dictionary for storage"""
        return {
            "product_selected": self.product_selected,
            "product_details": self.product_details,
            "design_uploaded": self.design_uploaded,
            "design_path": self.design_path,
            "placement_selected": self.placement_selected,
            "placement": self.placement,
            "quantities_collected": self.quantities_collected,
            "sizes": self.sizes,
            "total_quantity": self.total_quantity,
            "total_price": self.total_price,
            "customer_info_collected": self.customer_info_collected,
            "customer_name": self.customer_name,
            "shipping_address": self.shipping_address,
            "email": self.email,
            "payment_url": self.payment_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderState':
        """Create an OrderState instance from a dictionary"""
        order = cls()
        for key, value in data.items():
            setattr(order, key, value)
        return order