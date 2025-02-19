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

    def create_invoice(self, order_state: 'OrderState') -> Dict:
        """
        Create a PayPal invoice for an order using OrderState
        
        Args:
            order_state: OrderState instance containing all order details
        """
        logger.info("Starting PayPal invoice creation for order")
        
        # Log input validation
        logger.debug("Validating order state - Name: %s, Email: %s, Address: %s", 
                     order_state.customer_name, 
                     order_state.email, 
                     order_state.shipping_address)
        
        # Log order details
        logger.debug("Order details - Product: %s, Color: %s, Placement: %s", 
                     order_state.product_details.get('product_name'),
                     order_state.product_details.get('color'),
                     order_state.placement)
        
        # Log quantities
        logger.debug("Order quantities: %s", str(order_state.sizes))

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
            logger.debug("Formatted address: %s", str(address))

            # Prepare items list
            items = []
            for size, quantity in order_state.sizes.items():
                items.append({
                    "name": f"{order_state.product_details['product_name']} - Size {size.upper()}",
                    "description": f"Color: {order_state.product_details['color']}, Placement: {order_state.placement}",
                    "quantity": str(quantity),
                    "unit_amount": {
                        "currency_code": "USD",
                        "value": str(order_state.total_price / order_state.total_quantity)
                    }
                })
            logger.debug("Prepared invoice items: %s", str(items))

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
                        "name": {
                            "given_name": order_state.customer_name.split()[0],
                            "surname": " ".join(order_state.customer_name.split()[1:]) if len(order_state.customer_name.split()) > 1 else ""
                        },
                        "email_address": order_state.email,
                        "address": address
                    }
                }],
                "items": items
            }
            logger.debug("Preparing PayPal invoice request data: %s", str(invoice_data))

            response = requests.post(
                invoice_url,
                headers=headers,
                json=invoice_data
            )
            logger.debug("PayPal create invoice response status: %s", response.status_code)
            
            # Log raw response before JSON parsing
            logger.debug("Raw PayPal response: %s", response.text)
            
            response.raise_for_status()
            
            invoice_data = response.json()
            logger.debug("Raw PayPal response data after JSON parse: %s", str(invoice_data))

            # Extract invoice ID from href
            if 'href' in invoice_data:
                invoice_id = invoice_data['href'].split('/')[-1]
                logger.debug("Extracted invoice ID from href: %s", invoice_id)
                # Strip off "INV2" prefix and remove hyphens
                if invoice_id.startswith("INV2"):
                    payment_url_id = invoice_id[4:].replace("-", "")
                else:
                    payment_url_id = invoice_id.replace("-", "")
                logger.debug("Formatted payment URL ID: %s", payment_url_id)
            else:
                logger.error("PayPal response missing 'href' field. Full response: %s", str(invoice_data))
                raise ValueError("PayPal API response missing required 'href' field")
            
            # Send the invoice
            logger.debug("Attempting to send invoice ID: %s", invoice_id)
            send_response = requests.post(
                f"{invoice_url}/{invoice_id}/send",
                headers=headers
            )
            logger.debug("PayPal send invoice response status: %s", send_response.status_code)
            # Log raw send response
            logger.debug("Raw PayPal send response: %s", send_response.text)
            
            send_response.raise_for_status()

            return {
                "invoice_id": invoice_id,
                "status": "SENT",
                "invoice_number": invoice_id,
                "payment_url": f"https://www.paypal.com/invoice/p/#{payment_url_id}"
            }

        except requests.exceptions.RequestException as e:
            logger.error("PayPal API error during invoice creation: %s. Response: %s", 
                         str(e), 
                         getattr(e.response, 'text', 'No response text'))
            raise
        except Exception as e:
            logger.error("Unexpected error during invoice creation: %s", str(e), exc_info=True)
            raise