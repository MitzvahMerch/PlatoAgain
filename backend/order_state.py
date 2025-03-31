from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import pytz

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
    has_logo: bool = True  # Default to True - every design has a logo charge

@dataclass
class OrderState:
    """Tracks the state of an order through the sales process"""
    
    # User/Session Info
    user_id: str = None
    last_active: datetime = None
    
    # Product Selection
    product_selected: bool = False
    product_details: Optional[Dict] = None  # Includes name, color, style, price, images
    product_category: Optional[str] = None  # Store the product category (T-Shirt, Sweatshirt, etc.)
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
    
    # New fields for product selection intent
    original_intent: Dict = field(default_factory=lambda: {"category": None, "general_color": None, "requested_changes": []})
    in_product_modification_flow: bool = False
    
    # Quantities
    quantities_collected: bool = False
    sizes: Optional[Dict[str, int]] = None
    total_quantity: int = 0
    total_price: float = 0

    # Logo tracking for price calculations
    logo_count: int = 0  # Track number of logos uploaded
    logo_charge_per_item: float = 1.50  # $1.50 charge per logo per item
    
    color_options_style: Optional[str] = None
    color_options_product_name: Optional[str] = None
    
    # Customer Information
    customer_info_collected: bool = False
    customer_name: Optional[str] = None
    shipping_address: Optional[str] = None
    email: Optional[str] = None
    received_by_date: Optional[str] = None  # Field for target delivery date
    
    # Express shipping charge tracking
    express_shipping_charge: float = 0  # Additional charge for express shipping
    express_shipping_percentage: float = 0  # Percentage applied for express shipping
    
    # Payment Information
    payment_info_collected: bool = False
    payment_url: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    payment_status: Optional[str] = None
    
    # Order Status
    status: str = 'in_progress'  # in_progress, pending_review, approved, completed
    color_options_shown: bool = False
    last_style_number: Optional[str] = None
    
    def update_product(self, details: Dict):
        """Update product selection details while preserving design information"""
        # Store the current values to log them for debugging
        previous_design_count = len(self.designs) if hasattr(self, 'designs') else 0
        previous_logo_count = self.logo_count if hasattr(self, 'logo_count') else 0
    
        # Update product details
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
    
        # Explicitly verify design information is intact after product update
        current_design_count = len(self.designs) if hasattr(self, 'designs') else 0
        current_logo_count = self.logo_count if hasattr(self, 'logo_count') else 0
    
        # Log whether design information was preserved
        logger.info(f"Product updated: designs {previous_design_count}->{current_design_count}, logos {previous_logo_count}->{current_logo_count}")
    
        # If quantities are already collected, update the total price with the new product price
        if self.quantities_collected and self.total_quantity > 0:
            self.update_total_price()
    
    def update_original_intent(self, category: Optional[str] = None, general_color: Optional[str] = None):
        """Store or update the original user intent for product selection"""
        logger.info(f"Updating original intent: category='{category}', general_color='{general_color}'")
        
        if category:
            self.original_intent["category"] = category
        if general_color:
            self.original_intent["general_color"] = general_color
        
        logger.info(f"Original intent updated: {self.original_intent}")
    
    def add_requested_change(self, change_request: str):
        """Add a new requested change to the original intent"""
        logger.info(f"Adding requested change: '{change_request}'")
        self.original_intent["requested_changes"].append(change_request)
        logger.info(f"Requested changes updated: {self.original_intent['requested_changes']}")
    
    def update_design(self, design_path: str, filename: str = None, file_type: str = None, file_size: int = None, side: str = 'front', has_logo: bool = True):
        """Update design information - now supports multiple designs"""
        logger.info(f"Adding design: {design_path}, side: {side}, has_logo: {has_logo}")
        
        # Create a new design entry
        design = DesignInfo(
            design_path=design_path,
            design_filename=filename,
            design_file_type=file_type,
            design_file_size=file_size,
            upload_date=datetime.now(),
            side=side,
            has_logo=has_logo
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
        
        # Only increment logo count if this design has a logo charge
        if has_logo:
            self.logo_count += 1
            logger.info(f"Incremented logo count to {self.logo_count}, charging ${self.logo_charge_per_item} per logo per item")
        
        # If quantities already collected, update total price to include logo charge
        if self.quantities_collected and self.total_quantity > 0:
            self.update_total_price()
        
        logger.info(f"Design added successfully. Total designs: {len(self.designs)}, Logo count: {self.logo_count}")
    
    def update_total_price(self):
        """Calculate total price including base price, logo charges, and express shipping charges"""
        # Verify logo count matches the number of designs with has_logo=True
        logo_designs = sum(1 for design in self.designs if getattr(design, 'has_logo', True))
    
        if self.logo_count != logo_designs:
            logger.warning(f"Logo count mismatch: tracked={self.logo_count}, actual={logo_designs}. Correcting...")
            # Log each design to identify the problem
            for i, design in enumerate(self.designs):
                logger.warning(f"Design {i}: has_logo={getattr(design, 'has_logo', True)}")
            # Actually fix the logo count to match the designs
            self.logo_count = logo_designs
    
        old_total_price = self.total_price
    
        # Calculate base product price
        base_price = self.total_quantity * self.price_per_item
    
        # Calculate logo charges: $1.50 per logo PER ITEM
        logo_charges = self.total_quantity * self.logo_count * self.logo_charge_per_item
    
        logger.info(f"Calculating logo charges: {self.total_quantity} items × {self.logo_count} logos × ${self.logo_charge_per_item} = ${logo_charges:.2f}")
    
        # Calculate subtotal (before express shipping)
        subtotal = base_price + logo_charges
    
        # Apply express shipping percentage if applicable
        if self.express_shipping_percentage > 0:
            self.express_shipping_charge = subtotal * (self.express_shipping_percentage / 100)
            logger.info(f"Applied {self.express_shipping_percentage}% express shipping charge: ${self.express_shipping_charge:.2f}")
        else:
            self.express_shipping_charge = 0
        
        # Calculate final total price
        self.total_price = subtotal + self.express_shipping_charge
    
        logger.info(f"Updated total price from ${old_total_price:.2f} to ${self.total_price:.2f}")
        logger.info(f"Price breakdown: base=${base_price:.2f}, logo charges=${logo_charges:.2f} ({self.logo_count} logos × {self.total_quantity} items × ${self.logo_charge_per_item}), express shipping=${self.express_shipping_charge:.2f}")
    
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
        
        # Check and update logo count based on actual designs
        if self.designs:
            logo_designs = sum(1 for design in self.designs if getattr(design, 'has_logo', True))
            if self.logo_count != logo_designs:
                logger.warning(f"Logo count mismatch during placement: tracked={self.logo_count}, actual={logo_designs}. Correcting...")
                self.logo_count = logo_designs
                
                # Update total price if quantities are already collected
                if self.quantities_collected and self.total_quantity > 0:
                    self.update_total_price()
        
        logger.info(f"Placement updated successfully, placement_selected={self.placement_selected}, placement={self.placement}")
    
    def update_quantities(self, sizes: Dict[str, int]):
        """Update quantities and calculate totals"""
        self.quantities_collected = True
        self.sizes = sizes
        self.total_quantity = sum(sizes.values())
        
        # Ensure we have the correct logo count based on designs
        if self.designs:
            logo_designs = sum(1 for design in self.designs if getattr(design, 'has_logo', True))
            if self.logo_count != logo_designs:
                logger.warning(f"Logo count mismatch during quantity update: tracked={self.logo_count}, actual={logo_designs}. Correcting...")
                self.logo_count = logo_designs
        
        if self.price_per_item > 0:
            # Use update_total_price to calculate with logo charges
            self.update_total_price()
    
    def _calculate_express_shipping_percentage(self, received_by_date: str) -> float:
        """Calculate the express shipping percentage based on received_by_date"""
        try:
            # Parse the received_by_date (MM/DD/YYYY format)
            if not received_by_date:
                return 0
                
            received_date = datetime.strptime(received_by_date, "%m/%d/%Y")
            
            # Use Eastern Time as standard reference, regardless of server location
            eastern_tz = pytz.timezone('America/New_York')
            now = datetime.now(eastern_tz)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Strip tzinfo to make it a naive datetime for consistent comparisons
            today = today.replace(tzinfo=None)
            
            # Calculate free standard shipping date (today + 17 days)
            free_shipping_date = today + timedelta(days=17)
            
            # Log the dates for debugging
            logger.info(f"Calculating express shipping with Eastern Time: today={today.strftime('%m/%d/%Y')}, " +
                        f"free_shipping_date={free_shipping_date.strftime('%m/%d/%Y')}, " +
                        f"received_by_date={received_by_date}")
            
            # If the received date is ON or AFTER the free shipping date, no express charge
            if received_date >= free_shipping_date:
                logger.info("Standard shipping selected (no additional charge)")
                return 0
                
            # Calculate days before free shipping date
            days_before_free = (free_shipping_date - received_date).days
            
            # Apply appropriate shipping charge based on days before free shipping date
            if days_before_free <= 0:
                # Standard or later shipping - no additional charge
                logger.info("Standard shipping selected (no additional charge)")
                return 0
            elif days_before_free <= 2:
                # 1-2 days before suggested - 10% charge
                logger.info(f"Express shipping tier 1 selected (+10% charge, {days_before_free} days before free shipping)")
                return 10
            elif days_before_free <= 4:
                # 3-4 days before suggested - 20% charge
                logger.info(f"Express shipping tier 2 selected (+20% charge, {days_before_free} days before free shipping)")
                return 20
            elif days_before_free <= 6:
                # 5-6 days before suggested - 30% charge
                logger.info(f"Express shipping tier 3 selected (+30% charge, {days_before_free} days before free shipping)")
                return 30
            else:
                # More than 6 days before free shipping - not allowed
                logger.warning(f"Requested delivery date {received_by_date} is too early (more than 6 days before free shipping)")
                return 0
        except Exception as e:
            logger.error(f"Error calculating express shipping percentage: {e}")
            return 0
    
    def update_customer_info(self, name: str, address: str, email: str, received_by_date: str = None):
        """Update customer information"""
        logger.info(f"BEFORE update_customer_info: quantities_collected={self.quantities_collected}")
        
        # Log previous values if they exist
        if self.customer_name or self.shipping_address or self.email or self.received_by_date:
            logger.info(f"Previous customer info: name='{self.customer_name}', address='{self.shipping_address}', email='{self.email}', received_by_date='{self.received_by_date}'")
        
        # Update the customer information values
        self.customer_info_collected = True
        self.customer_name = name
        self.shipping_address = address
        self.email = email
        self.received_by_date = received_by_date
        
        # Calculate and apply express shipping percentage based on received_by_date
        if received_by_date:
            old_percentage = self.express_shipping_percentage
            self.express_shipping_percentage = self._calculate_express_shipping_percentage(received_by_date)
            
            # If the percentage changed and quantities are collected, update the total price
            if old_percentage != self.express_shipping_percentage and self.quantities_collected:
                logger.info(f"Express shipping percentage changed from {old_percentage}% to {self.express_shipping_percentage}%")
                self.update_total_price()
        
        logger.info(f"Customer info updated successfully, customer_info_collected={self.customer_info_collected}")
        logger.info(f"Updated values: name='{self.customer_name}', address='{self.shipping_address}', email='{self.email}', received_by_date='{self.received_by_date}'")
        if self.express_shipping_percentage > 0:
            logger.info(f"Express shipping fee applied: {self.express_shipping_percentage}% (${self.express_shipping_charge:.2f})")
        
        logger.info(f"AFTER update_customer_info: quantities_collected={self.quantities_collected}")

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
    
    def to_dict(self) -> Dict:
        """Convert the order state to a standardized dictionary format for all persistence needs"""
        # Log the start of the method
        logger.info(f"to_dict called with quantities_collected={self.quantities_collected}")
        
        # Calculate total logo charges
        logo_charges = self.total_quantity * self.logo_count * self.logo_charge_per_item
        
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
                'has_logo': getattr(design, 'has_logo', True),
                'index': idx
            })
        
        # Create a flat dictionary with all properties
        result = {
            "user_id": self.user_id,
            "last_active": self.last_active,
            
            # Product Selection
            "product_selected": self.product_selected,
            "product_details": self.product_details,
            "product_category": self.product_category,
            "youth_sizes": self.youth_sizes,
            "adult_sizes": self.adult_sizes,
            "price_per_item": self.price_per_item,
            
            # Design Info
            "design_uploaded": self.design_uploaded,
            "designs": designs_list,
            "design_path": self.design_path,
            "design_filename": self.design_filename,
            "design_file_type": self.design_file_type,
            "design_file_size": self.design_file_size,
            "upload_date": self.upload_date,
            
            # Placement Info
            "placement_selected": self.placement_selected,
            "placement": self.placement,
            "preview_url": self.preview_url,
            "rejected_products": self.rejected_products,
            
            # Intent Info
            "original_intent": self.original_intent,
            "in_product_modification_flow": self.in_product_modification_flow,
            
            # Quantity Info
            "quantities_collected": self.quantities_collected, 
            "sizes": self.sizes,
            "total_quantity": self.total_quantity,
            "total_price": self.total_price,
            "logo_count": self.logo_count,
            "logo_charge_per_item": self.logo_charge_per_item,
            
            # UI state
            "color_options_shown": self.color_options_shown,
            "color_options_style": self.color_options_style,
            "color_options_product_name": self.color_options_product_name,
            "last_style_number": self.last_style_number,
            
            # Shipping Info
            "express_shipping_percentage": self.express_shipping_percentage,
            "express_shipping_charge": self.express_shipping_charge,
            
            # Customer Info
            "customer_info_collected": self.customer_info_collected,
            "customer_name": self.customer_name,
            "shipping_address": self.shipping_address,
            "email": self.email,
            "received_by_date": self.received_by_date,
            
            # Payment Info
            "payment_info_collected": self.payment_info_collected,
            "payment_url": self.payment_url,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "payment_status": self.payment_status,
            
            # Other
            "status": self.status
        }
        
        # Log key fields for debugging
        logger.info(f"Result of to_dict has quantities_collected={result['quantities_collected']}")
        if 'payment_url' in result and result['payment_url']:
            logger.info(f"Payment URL in dict: {result['payment_url']}")
        
        return result
    
    # Remove to_firestore_dict() completely - we'll now use to_dict() for all persistence
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderState':
        """Create an OrderState instance from a dictionary with simplified logic"""
        order = cls()
        
        # Log the input data structure
        logger.info(f"from_dict called with data keys: {list(data.keys())}")
        
        # Handle designs list specially
        if 'designs' in data and isinstance(data['designs'], list):
            for design_data in data['designs']:
                # Handle both flattened and nested design formats
                design = DesignInfo(
                    design_path=design_data.get('design_path') or design_data.get('designPath'),
                    design_filename=design_data.get('design_filename') or design_data.get('filename'),
                    design_file_type=design_data.get('design_file_type') or design_data.get('fileType'),
                    design_file_size=design_data.get('design_file_size') or design_data.get('fileSize'),
                    upload_date=design_data.get('upload_date') or design_data.get('uploadDate'),
                    placement=design_data.get('placement'),
                    preview_url=design_data.get('preview_url') or design_data.get('previewUrl'),
                    side=design_data.get('side'),
                    has_logo=design_data.get('has_logo', True) or design_data.get('hasLogo', True)
                )
                order.designs.append(design)
        
        # Handle old nested structure (transitional code)
        if 'designInfo' in data and isinstance(data['designInfo'], dict):
            # Extract design_uploaded from nested structure
            if 'uploaded' in data['designInfo'] and not order.design_uploaded:
                order.design_uploaded = data['designInfo']['uploaded']
            
            # Extract nested designs if not already handled above
            if 'designs' in data['designInfo'] and not order.designs:
                for design_data in data['designInfo']['designs']:
                    design = DesignInfo(
                        design_path=design_data.get('designPath'),
                        design_filename=design_data.get('filename'),
                        design_file_type=design_data.get('fileType'),
                        design_file_size=design_data.get('fileSize'),
                        upload_date=design_data.get('uploadDate'),
                        placement=design_data.get('placement'),
                        preview_url=design_data.get('previewUrl'),
                        side=design_data.get('side'),
                        has_logo=design_data.get('hasLogo', True)
                    )
                    order.designs.append(design)
                    
            # Extract logo count if available
            if 'logoCount' in data['designInfo']:
                order.logo_count = data['designInfo']['logoCount']
        
        # Handle old product info structure (transitional code)
        if 'productInfo' in data and isinstance(data['productInfo'], dict):
            product_info = data['productInfo']
            if 'selected' in product_info and not order.product_selected:
                order.product_selected = product_info['selected']
            if 'details' in product_info and not order.product_details:
                order.product_details = product_info['details']
            if 'category' in product_info and not order.product_category:
                order.product_category = product_info['category']
            if 'pricePerItem' in product_info and order.price_per_item == 0:
                order.price_per_item = product_info['pricePerItem']
        
        # Handle old quantity info structure (transitional code)
        if 'quantityInfo' in data and isinstance(data['quantityInfo'], dict):
            quantity_info = data['quantityInfo']
            if 'collected' in quantity_info and not order.quantities_collected:
                order.quantities_collected = quantity_info['collected']
            if 'sizes' in quantity_info and not order.sizes:
                order.sizes = quantity_info['sizes']
            if 'totalQuantity' in quantity_info and order.total_quantity == 0:
                order.total_quantity = quantity_info['totalQuantity']
            if 'totalPrice' in quantity_info and order.total_price == 0:
                order.total_price = quantity_info['totalPrice']
            if 'logoChargePerItem' in quantity_info and order.logo_charge_per_item == 1.5:
                order.logo_charge_per_item = quantity_info['logoChargePerItem']
        
        # Handle other flattened fields directly
        for key, value in data.items():
            # Skip already processed or non-existent fields
            if key in ('designs', 'designInfo', 'productInfo', 'quantityInfo', 'placementInfo', 
                       'customerInfo', 'paymentInfo', 'expressShippingInfo', 'originalIntent') or not hasattr(order, key):
                continue
                
            # Set the attribute if it exists in the class
            setattr(order, key, value)
        
        # Handle original intent data from both structures
        if 'original_intent' in data:
            # Map from camelCase to snake_case
            intent_data = data['originalIntent']
            order.original_intent = {
                "category": intent_data.get('category'),
                "general_color": intent_data.get('generalColor'),
                "requested_changes": intent_data.get('requestedChanges', [])
            }
        
        # Verify logo count matches designs immediately after loading
        if order.designs:
            logo_designs = sum(1 for design in order.designs if getattr(design, 'has_logo', True))
            if order.logo_count != logo_designs:
                logger.warning(f"Logo count mismatch in from_dict: {order.logo_count} -> {logo_designs}")
                order.logo_count = logo_designs
        
        # Ensure essential fields have proper defaults
        if not hasattr(order, 'express_shipping_percentage') or order.express_shipping_percentage is None:
            order.express_shipping_percentage = 0
        if not hasattr(order, 'express_shipping_charge') or order.express_shipping_charge is None:
            order.express_shipping_charge = 0
        
        logger.info(f"Successfully created OrderState from dictionary, quantities_collected={order.quantities_collected}")
        return order