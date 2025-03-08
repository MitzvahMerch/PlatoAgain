from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class DesignInfo:
    """Stores information about a single design in an order"""
    
    design_path: Optional[str] = None  # Full Firebase Storage URL
    design_filename: Optional[str] = None
    design_file_type: Optional[str] = None
    design_file_size: Optional[int] = None
    upload_date: Optional[datetime] = None
    placement: Optional[str] = None
    preview_url: Optional[str] = None  # URL to preview image
    side: Optional[str] = None  # 'front' or 'back'

@dataclass
class OrderState:
    """Tracks the state of an order through the sales process"""
    
    # User/Session Info
    user_id: str = None
    last_active: datetime = None
    
    # Product Selection
    product_selected: bool = False
    product_details: Optional[Dict] = None # Includes name, color, style, price, images
    product_category: Optional[str] = None # Store the product category (T-Shirt, Sweatshirt, etc.)
    youth_sizes: Optional[str] = None
    adult_sizes: Optional[str] = None
    price_per_item: float = 0
    
    # Design Info (supports multiple designs)
    design_uploaded: bool = False
    designs: List[DesignInfo] = field(default_factory=list)
    # Legacy fields for backward compatibility
    design_path: Optional[str] = None
    design_filename: Optional[str] = None
    design_file_type: Optional[str] = None
    design_file_size: Optional[int] = None
    upload_date: Optional[datetime] = None
    
    # Placement Info
    placement_selected: bool = False
    placement: Optional[str] = None
    preview_url: Optional[str] = None  # URL to preview image
    rejected_products: List[Dict] = field(default_factory=list)
    
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
    received_by_date: Optional[str] = None  # New field for target delivery date
    
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
        
        # Save the product category if provided
        if 'category' in details:
            self.product_category = details['category']
        if 'youth_sizes' in details:
            self.youth_sizes = details['youth_sizes']
        if 'adult_sizes' in details:
            self.adult_sizes = details['adult_sizes']
        if 'price' in details:
            self.price_per_item = float(details['price'].replace('$', ''))
    
    def update_design(self, design_path: str, filename: str = None, file_type: str = None, file_size: int = None, side: str = 'front'):
        """Update design information - now supports multiple designs"""
        logger.info(f"Adding design: {design_path}, side: {side}")
        
        # Create a new design entry
        design = DesignInfo(
            design_path=design_path,
            design_filename=filename,
            design_file_type=file_type,
            design_file_size=file_size,
            upload_date=datetime.now(),
            side=side
        )
        
        # Add to the designs list
        self.designs.append(design)
        
        # Update legacy fields for backward compatibility
        self.design_uploaded = True
        self.design_path = design_path
        self.design_filename = filename
        self.design_file_type = file_type
        self.design_file_size = file_size
        self.upload_date = datetime.now()
        
        logger.info(f"Design added successfully. Total designs: {len(self.designs)}")
    
    def update_placement(self, placement: str, preview_url: Optional[str] = None, design_index: int = -1):
        """Update design placement and preview for a specific design"""
        logger.info(f"Updating placement for design index {design_index}: placement={placement}, preview_url={preview_url}")
        
        # Set the placement_selected flag
        self.placement_selected = True
        
        # Update the legacy fields for backward compatibility
        self.placement = "Custom"
        self.preview_url = preview_url
        
        # Update the placement for the specific design
        if self.designs and design_index < len(self.designs) and design_index >= -len(self.designs):
            design = self.designs[design_index]
            design.placement = placement
            design.preview_url = preview_url
            logger.info(f"Placement updated for design {design_index}")
        else:
            logger.warning(f"Could not update placement: design index {design_index} out of range (total designs: {len(self.designs)})")
        
        logger.info(f"Placement updated successfully, placement_selected={self.placement_selected}, placement={self.placement}")
    
    def update_quantities(self, sizes: Dict[str, int]):
        """Update quantities and calculate totals"""
        self.quantities_collected = True
        self.sizes = sizes
        self.total_quantity = sum(sizes.values())
        if self.price_per_item > 0:
            self.total_price = self.total_quantity * self.price_per_item
    
    def update_customer_info(self, name: str, address: str, email: str, received_by_date: str = None):
        """Update customer information"""
        logger.info(f"Updating customer info: name='{name}', address='{address}', email='{email}', received_by_date='{received_by_date}'")
        
        # Log previous values if they exist
        if self.customer_name or self.shipping_address or self.email or self.received_by_date:
            logger.info(f"Previous customer info: name='{self.customer_name}', address='{self.shipping_address}', email='{self.email}', received_by_date='{self.received_by_date}'")
        
        # Update the values
        self.customer_info_collected = True
        self.customer_name = name
        self.shipping_address = address
        self.email = email
        self.received_by_date = received_by_date
        
        logger.info(f"Customer info updated successfully, customer_info_collected={self.customer_info_collected}")
        logger.info(f"Updated values: name='{self.customer_name}', address='{self.shipping_address}', email='{self.email}', received_by_date='{self.received_by_date}'")

    def add_rejected_product(self, product_info: Dict):
        """Add a product to the rejected products list"""
        if self.product_details:
            self.rejected_products.append(self.product_details)
        # Update the current product
        self.product_selected = False
        self.product_details = None
    
    def update_payment_info(self, invoice_data: Dict):
        """Update payment information from PayPal response"""
        logger.info(f"Updating payment info with invoice data: {invoice_data}")
        
        # Log previous values if they exist
        if any([self.payment_url, self.invoice_id, self.invoice_number, self.payment_status]):
            logger.info(f"Previous payment info: payment_url='{self.payment_url}', invoice_id='{self.invoice_id}', invoice_number='{self.invoice_number}', status='{self.payment_status}'")
        
        # Update the values
        self.payment_info_collected = True
        self.payment_url = invoice_data.get('payment_url')
        self.invoice_id = invoice_data.get('invoice_id')
        self.invoice_number = invoice_data.get('invoice_number')
        self.payment_status = invoice_data.get('status')
        
        # Log the updated values
        logger.info(f"Payment info updated successfully, payment_info_collected={self.payment_info_collected}")
        logger.info(f"Updated values: payment_url='{self.payment_url}', invoice_id='{self.invoice_id}', invoice_number='{self.invoice_number}', status='{self.payment_status}'")
        
        # Log warnings for any missing values
        if not self.payment_url:
            logger.warning("Payment URL is missing in the updated payment info")
        if not self.invoice_id:
            logger.warning("Invoice ID is missing in the updated payment info")
        if not self.invoice_number:
            logger.warning("Invoice number is missing in the updated payment info")
        if not self.payment_status:
            logger.warning("Payment status is missing in the updated payment info")
    
    def update_status(self, status: str):
        """Update order status"""
        logger.info(f"Updating order status from '{self.status}' to '{status}'")
        self.status = status
        logger.info(f"Order status updated successfully to '{self.status}'")
    
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
        logger.info("Checking if order is complete")
        
        # Check each required condition separately for better logging
        product_check = self.product_selected
        design_check = self.design_uploaded
        # Removed placement_check since it's no longer required
        quantities_check = self.quantities_collected
        customer_info_check = self.customer_info_collected
        
        # Log the state of each condition
        logger.info(f"Order completeness check - product_selected: {product_check}")
        logger.info(f"Order completeness check - design_uploaded: {design_check}")
        logger.info(f"Order completeness check - quantities_collected: {quantities_check}")
        logger.info(f"Order completeness check - customer_info_collected: {customer_info_check}")
        
        # Perform the completeness check (removed placement_check)
        is_complete = all([
            product_check,
            design_check,
            quantities_check,
            customer_info_check
        ])
        
        logger.info(f"Order completeness result: {is_complete}")
        
        if not is_complete:
            # Log which specific conditions failed
            missing_steps = []
            if not product_check:
                missing_steps.append("product selection")
            if not design_check:
                missing_steps.append("design upload")
            if not quantities_check:
                missing_steps.append("quantities collection")
            if not customer_info_check:
                missing_steps.append("customer information")
            
            logger.warning(f"Order is incomplete. Missing steps: {', '.join(missing_steps)}")
        
        return is_complete
    
    def to_firestore_dict(self) -> Dict:
        """Convert the order state to a dictionary for Firestore storage"""
        logger.debug("Converting order state to Firestore dictionary")
        
        # Convert the designs list to a list of dictionaries
        designs_list = []
        for idx, design in enumerate(self.designs):
            designs_list.append({
                'designPath': design.design_path,
                'filename': design.design_filename,
                'fileType': design.design_file_type,
                'fileSize': design.design_file_size,
                'uploadDate': design.upload_date,
                'placement': design.placement,
                'previewUrl': design.preview_url,
                'side': design.side,
                'index': idx
            })
        
        result = {
            'userId': self.user_id,
            'productInfo': {
                'selected': self.product_selected,
                'details': self.product_details,
                'category': self.product_category,
                'pricePerItem': self.price_per_item
            },
            'designInfo': {
                'uploaded': self.design_uploaded,
                'designs': designs_list,
                # Include the legacy fields for backward compatibility
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
                'email': self.email,
                'receivedByDate': self.received_by_date
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
        
        # Log payment URL specifically since it's causing issues
        logger.info(f"Payment URL in Firestore dict: {result['paymentInfo']['paymentUrl']}")
        
        return result
    
    def to_dict(self) -> Dict:
        """Convert the order state to a flat dictionary for internal use"""
        # Convert the designs list to a list of dictionaries
        designs_list = []
        for idx, design in enumerate(self.designs):
            designs_list.append({
                'design_path': design.design_path,
                'design_filename': design.design_filename,
                'design_file_type': design.design_file_type,
                'design_file_size': design.design_file_size,
                'upload_date': design.upload_date,
                'placement': design.placement,
                'preview_url': design.preview_url,
                'side': design.side,
                'index': idx
            })
            
        return {
            "user_id": self.user_id,
            "product_selected": self.product_selected,
            "product_details": self.product_details,
            "product_category": self.product_category,
            "price_per_item": self.price_per_item,
            "design_uploaded": self.design_uploaded,
            "designs": designs_list,
            # Include legacy fields for backward compatibility
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
            "received_by_date": self.received_by_date,
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
        
        # Handle the designs list separately if it exists
        if 'designs' in data:
            designs_data = data.pop('designs')
            for design_data in designs_data:
                design = DesignInfo(
                    design_path=design_data.get('design_path'),
                    design_filename=design_data.get('design_filename'),
                    design_file_type=design_data.get('design_file_type'),
                    design_file_size=design_data.get('design_file_size'),
                    upload_date=design_data.get('upload_date'),
                    placement=design_data.get('placement'),
                    preview_url=design_data.get('preview_url'),
                    side=design_data.get('side')
                )
                order.designs.append(design)
        
        # Set all the other fields
        for key, value in data.items():
            if hasattr(order, key):
                setattr(order, key, value)
                
        return order