import logging
import requests
from typing import Dict
from datetime import datetime, timedelta
from config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        """Initialize PayPal service with credentials from config"""
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self.base_url = "https://api-m.paypal.com"
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> str:
        """Get or refresh PayPal access token"""
        logger.debug("Checking if access token refresh is needed")
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        auth_url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(
                auth_url,
                auth=(self.client_id, self.client_secret),
                headers=headers,
                data=data
            )
            logger.debug("PayPal auth response status: %s", response.status_code)
            response.raise_for_status()
            
            token_data = response.json()
            logger.debug("Successfully obtained new access token, expires in %s seconds", token_data["expires_in"])
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
            
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error("PayPal authentication failed: %s. Response: %s", str(e), getattr(e.response, 'text', 'No response text'))
            raise

    def _validate_order_state(self, order_state: 'OrderState') -> bool:
        """Validate order state has all required information for PayPal invoice"""
        required_fields = {
            'customer_name': order_state.customer_name,
            'email': order_state.email,
            'shipping_address': order_state.shipping_address,
            'product_details': order_state.product_details,
            'sizes': order_state.sizes,
            'total_quantity': order_state.total_quantity,
            'total_price': order_state.total_price
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            logger.error(f"Missing required fields for PayPal invoice: {', '.join(missing_fields)}")
            return False
            
        return True

    def create_invoice(self, order_state: 'OrderState') -> Dict:
        """
        Create a PayPal invoice for an order using OrderState
        
        Args:
            order_state: OrderState instance containing all order details
        
        Returns:
            Dict containing invoice_id, status, invoice_number, and payment_url
        
        Raises:
            ValueError: If order_state is missing required information
            RequestException: If PayPal API request fails
        """
        logger.info("Starting PayPal invoice creation for order")
        
        # Validate order state
        if not self._validate_order_state(order_state):
            raise ValueError("Order state missing required information for PayPal invoice")
        
        # Log order details
        logger.debug("Creating invoice for order - Product: %s, Total: $%.2f, Quantity: %d", 
                     order_state.product_details.get('product_name'),
                     order_state.total_price,
                     order_state.total_quantity)

        try:
            access_token = self._get_access_token()
            
            invoice_url = f"{self.base_url}/v2/invoicing/invoices"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Format shipping address
            address_parts = order_state.shipping_address.split(",")
            address = {
                "address_line_1": address_parts[0].strip(),
                "city": address_parts[1].strip() if len(address_parts) > 1 else "",
                "state": address_parts[2].strip() if len(address_parts) > 2 else "",
                "postal_code": address_parts[3].strip() if len(address_parts) > 3 else "",
                "country_code": "US"
            }

            # Calculate unit price
            unit_price = order_state.total_price / order_state.total_quantity
            
            # Prepare items list
            items = []
            for size, quantity in order_state.sizes.items():
                items.append({
                    "name": f"{order_state.product_details['product_name']} - Size {size.upper()}",
                    "description": (f"Color: {order_state.product_details['color']}, "
                                  f"Placement: {order_state.placement}"),
                    "quantity": str(quantity),
                    "unit_amount": {
                        "currency_code": "USD",
                        "value": f"{unit_price:.2f}"
                    }
                })

            # Prepare customer name
            name_parts = order_state.customer_name.split()
            customer_name = {
                "given_name": name_parts[0],
                "surname": " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            }

            invoice_data = {
                "detail": {
                    "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "currency_code": "USD",
                    "payment_term": {
                        "term_type": "DUE_ON_RECEIPT"
                    }
                },
                "primary_recipients": [{
                    "billing_info": {
                        "name": customer_name,
                        "email_address": order_state.email,
                        "address": address
                    }
                }],
                "items": items
            }

            # Create invoice
            response = requests.post(invoice_url, headers=headers, json=invoice_data)
            response.raise_for_status()
            invoice_data = response.json()

            # Extract invoice ID and create payment URL
            if 'href' not in invoice_data:
                raise ValueError("PayPal API response missing required 'href' field")
                
            invoice_id = invoice_data['href'].split('/')[-1]
            payment_url_id = invoice_id[4:].replace("-", "") if invoice_id.startswith("INV2") else invoice_id.replace("-", "")
            
            # Send the invoice
            send_response = requests.post(
                f"{invoice_url}/{invoice_id}/send",
                headers=headers
            )
            send_response.raise_for_status()

            return {
                "invoice_id": invoice_id,
                "status": "SENT",
                "invoice_number": invoice_id,
                "payment_url": f"https://www.paypal.com/invoice/p/#{payment_url_id}"
            }

        except requests.exceptions.RequestException as e:
            logger.error("PayPal API error: %s. Response: %s", 
                        str(e), 
                        getattr(e.response, 'text', 'No response text'))
            raise
        except Exception as e:
            logger.error("Unexpected error during invoice creation: %s", str(e), exc_info=True)
            raise