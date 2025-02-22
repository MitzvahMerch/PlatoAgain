from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

@dataclass
class OrderState:
    """Tracks the state of an order through the sales process"""
    
    # User/Session Info
    user_id: str = None
    last_active: datetime = None
    
    # Product Selection
    product_selected: bool = False
    product_details: Optional[Dict] = None # Includes name, color, style, price, images
    price_per_item: float = 0
    
    # Design Info
    design_uploaded: bool = False
    design_path: Optional[str] = None  # Full Firebase Storage URL
    design_filename: Optional[str] = None
    design_file_type: Optional[str] = None
    design_file_size: Optional[int] = None
    upload_date: Optional[datetime] = None
    
    # Placement Info
    placement_selected: bool = False
    placement: Optional[str] = None
    preview_url: Optional[str] = None  # URL to preview image
    
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
    payment_info_collected: bool = False
    payment_url: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    payment_status: Optional[str] = None
    
    # Order Status
    status: str = 'in_progress'  # in_progress, pending_review, approved, completed
    
    def update_product(self, details: Dict):
        """Update product selection details"""
        self.product_selected = True
        self.product_details = details
        if 'price' in details:
            self.price_per_item = float(details['price'].replace('$', ''))
    
    def update_design(self, design_path: str, filename: str = None, file_type: str = None, file_size: int = None):
        """Update design information"""
        self.design_uploaded = True
        self.design_path = design_path
        self.design_filename = filename
        self.design_file_type = file_type
        self.design_file_size = file_size
        self.upload_date = datetime.now()
    
    def update_placement(self, placement: str, preview_url: Optional[str] = None):
        """Update design placement and preview"""
        self.placement_selected = True
        self.placement = "Custom"
        self.preview_url = preview_url
    
    def update_quantities(self, sizes: Dict[str, int]):
        """Update quantities and calculate totals"""
        self.quantities_collected = True
        self.sizes = sizes
        self.total_quantity = sum(sizes.values())
        if self.price_per_item > 0:
            self.total_price = self.total_quantity * self.price_per_item
    
    def update_customer_info(self, name: str, address: str, email: str):
        """Update customer information"""
        self.customer_info_collected = True
        self.customer_name = name
        self.shipping_address = address
        self.email = email
    
    def update_payment_info(self, invoice_data: Dict):
        """Update payment information from PayPal response"""
        self.payment_info_collected = True
        self.payment_url = invoice_data.get('payment_url')
        self.invoice_id = invoice_data.get('invoice_id')
        self.invoice_number = invoice_data.get('invoice_number')
        self.payment_status = invoice_data.get('status')
    
    def update_status(self, status: str):
        """Update order status"""
        self.status = status
    
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
    
    def to_firestore_dict(self) -> Dict:
        """Convert the order state to a dictionary for Firestore storage"""
        return {
            'userId': self.user_id,
            'productInfo': {
                'selected': self.product_selected,
                'details': self.product_details,
                'pricePerItem': self.price_per_item
            },
            'designInfo': {
                'uploaded': self.design_uploaded,
                'url': self.design_path,
                'filename': self.design_filename,
                'fileType': self.design_file_type,
                'fileSize': self.design_file_size,
                'uploadDate': self.upload_date
            },
            'placementInfo': {
                'selected': self.placement_selected,
                'placement': self.placement,
                'previewUrl': self.preview_url
            },
            'quantityInfo': {
                'collected': self.quantities_collected,
                'sizes': self.sizes,
                'totalQuantity': self.total_quantity,
                'totalPrice': self.total_price
            },
            'customerInfo': {
                'collected': self.customer_info_collected,
                'name': self.customer_name,
                'address': self.shipping_address,
                'email': self.email
            },
            'paymentInfo': {
                'collected': self.payment_info_collected,
                'paymentUrl': self.payment_url,
                'invoiceId': self.invoice_id,
                'invoiceNumber': self.invoice_number,
                'status': self.payment_status
            },
            'status': self.status,
            'lastActive': self.last_active
        }
    
    def to_dict(self) -> Dict:
        """Convert the order state to a flat dictionary for internal use"""
        return {
            "user_id": self.user_id,
            "product_selected": self.product_selected,
            "product_details": self.product_details,
            "price_per_item": self.price_per_item,
            "design_uploaded": self.design_uploaded,
            "design_path": self.design_path,
            "design_filename": self.design_filename,
            "design_file_type": self.design_file_type,
            "design_file_size": self.design_file_size,
            "upload_date": self.upload_date,
            "placement_selected": self.placement_selected,
            "placement": self.placement,
            "preview_url": self.preview_url,
            "quantities_collected": self.quantities_collected,
            "sizes": self.sizes,
            "total_quantity": self.total_quantity,
            "total_price": self.total_price,
            "customer_info_collected": self.customer_info_collected,
            "customer_name": self.customer_name,
            "shipping_address": self.shipping_address,
            "email": self.email,
            "payment_info_collected": self.payment_info_collected,
            "payment_url": self.payment_url,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "payment_status": self.payment_status,
            "status": self.status,
            "last_active": self.last_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderState':
        """Create an OrderState instance from a dictionary"""
        order = cls()
        for key, value in data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        return order