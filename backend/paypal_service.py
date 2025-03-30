import logging
import requests
import json
from typing import Dict
from datetime import datetime, timedelta
from config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        """Initialize PayPal service with credentials from config"""
        logger.info("Initializing PayPal service")
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self.base_url = "https://api-m.paypal.com"
        self.access_token = None
        self.token_expiry = None
        logger.info(f"PayPal service initialized with client_id: {self.client_id[:5]}... and base_url: {self.base_url}")

    def _get_access_token(self) -> str:
        """Get or refresh PayPal access token"""
        logger.info("Getting PayPal access token")
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("Reusing existing PayPal access token")
            return self.access_token

        auth_url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        data = {"grant_type": "client_credentials"}
        
        logger.info(f"Requesting new PayPal access token from {auth_url}")
        try:
            response = requests.post(
                auth_url,
                auth=(self.client_id, self.client_secret),
                headers=headers,
                data=data
            )
            logger.info(f"PayPal auth response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"PayPal auth failed with status {response.status_code}: {response.text}")
            
            response.raise_for_status()
            
            token_data = response.json()
            logger.info(f"Successfully obtained new access token, expires in {token_data['expires_in']} seconds")
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
            
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"PayPal authentication failed: {str(e)}. Response: {getattr(e.response, 'text', 'No response text')}")
            raise

    def _validate_order_state(self, order_state: 'OrderState') -> bool:
        """Validate order state has all required information for PayPal invoice"""
        logger.info("Validating order state for PayPal invoice")
        required_fields = {
            'customer_name': order_state.customer_name,
            'email': 'aaronamazon26@gmail.com',
            'shipping_address': order_state.shipping_address,
            'product_details': order_state.product_details,
            'sizes': order_state.sizes,
            'total_quantity': order_state.total_quantity,
            'total_price': order_state.total_price
        }
        
        # Log all field values for debugging
        for field, value in required_fields.items():
            logger.debug(f"Order state field '{field}': {value}")
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            logger.error(f"Missing required fields for PayPal invoice: {', '.join(missing_fields)}")
            return False
            
        logger.info("Order state validation successful for PayPal invoice")
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
        logger.info("Starting PayPal invoice creation process")
        
        # Validate order state
        logger.info("Validating order state before creating PayPal invoice")
        if not self._validate_order_state(order_state):
            logger.error("Order state validation failed - cannot create PayPal invoice")
            raise ValueError("Order state missing required information for PayPal invoice")
        
        # Log order details
        logger.info(f"Creating invoice for order - Product: {order_state.product_details.get('product_name')}, "
                   f"Total: ${order_state.total_price:.2f}, Quantity: {order_state.total_quantity}")
        logger.info(f"Customer details - Name: {order_state.customer_name}, "
                   f"Email: {'aaronamazon26@gmail.com'}, Address: {order_state.shipping_address}")

        try:
            # Get access token
            logger.info("Getting PayPal access token for invoice creation")
            access_token = self._get_access_token()
            logger.info("Successfully retrieved PayPal access token")
            
            # Prepare API call
            invoice_url = f"{self.base_url}/v2/invoicing/invoices"
            logger.info(f"Using PayPal invoice endpoint: {invoice_url}")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            logger.debug(f"Request headers: {headers}")

            # Format shipping address
            logger.info(f"Formatting shipping address: {order_state.shipping_address}")
            address_parts = order_state.shipping_address.split(",")
            
            # Log parsed address parts for debugging
            logger.debug(f"Address parts after splitting: {address_parts}")
            
            address = {
                "address_line_1": address_parts[0].strip(),
                "city": address_parts[1].strip() if len(address_parts) > 1 else "",
                "state": address_parts[2].strip() if len(address_parts) > 2 else "",
                "postal_code": address_parts[3].strip() if len(address_parts) > 3 else "",
                "country_code": "US"
            }
            logger.info(f"Formatted address: {address}")

            # Calculate unit price
            logger.info(f"Calculating unit price from total price: ${order_state.total_price:.2f} / {order_state.total_quantity} items")
            unit_price = order_state.total_price / order_state.total_quantity
            logger.info(f"Calculated unit price: ${unit_price:.2f}")
            
            # Prepare items list
            logger.info(f"Preparing invoice items from sizes: {order_state.sizes}")
            items = []
            for size, quantity in order_state.sizes.items():
                logger.debug(f"Adding item for size {size} with quantity {quantity}")
                items.append({
                    "name": f"{order_state.product_details['product_name']} - Size {size.upper()}",
                    "description": f"Color: {order_state.product_details['color']}",
                    "quantity": str(quantity),
                    "unit_amount": {
                        "currency_code": "USD",
                        "value": f"{unit_price:.2f}"
                    }
                })
            logger.info(f"Created {len(items)} invoice items")

            # Prepare customer name
            logger.info(f"Formatting customer name: {order_state.customer_name}")
            name_parts = order_state.customer_name.split()
            customer_name = {
                "given_name": name_parts[0],
                "surname": " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            }
            logger.info(f"Formatted customer name: {customer_name}")

            # Generate invoice number
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Generated invoice number: {invoice_number}")

            # Prepare invoice data
            invoice_data = {
                "detail": {
                    "invoice_number": invoice_number,
                    "currency_code": "USD",
                    "payment_term": {
                        "term_type": "DUE_ON_RECEIPT"
                    }
                },
                "primary_recipients": [{
                    "billing_info": {
                        "name": customer_name,
                        "email_address": "aaronamazon26@gmail.com",
                        "address": address
                    }
                }],
                "items": items
            }
            
            # Log the full invoice payload for debugging
            logger.debug(f"Full invoice payload: {json.dumps(invoice_data, indent=2)}")
            logger.info("Invoice payload prepared and ready for submission")

            # Create invoice
            logger.info("Sending invoice creation request to PayPal API")
            response = requests.post(invoice_url, headers=headers, json=invoice_data)
            logger.info(f"PayPal invoice creation response status: {response.status_code}")
            
            # Log response content for debugging
            try:
                response_content = response.json()
                logger.debug(f"PayPal API response: {json.dumps(response_content, indent=2)}")
            except ValueError:
                logger.debug(f"PayPal API response (non-JSON): {response.text}")
            
            # Check for error responses
            if response.status_code >= 400:
                logger.error(f"PayPal API error: HTTP {response.status_code} - {response.text}")
            
            response.raise_for_status()
            invoice_data = response.json()
            logger.info("PayPal invoice created successfully")

            # Extract invoice ID and create payment URL
            if 'href' not in invoice_data:
                logger.error(f"PayPal API response missing required 'href' field: {invoice_data}")
                raise ValueError("PayPal API response missing required 'href' field")
                
            invoice_id = invoice_data['href'].split('/')[-1]
            logger.info(f"Extracted invoice ID: {invoice_id}")
            
            payment_url_id = invoice_id[4:].replace("-", "") if invoice_id.startswith("INV2") else invoice_id.replace("-", "")
            logger.info(f"Formatted payment URL ID: {payment_url_id} (from invoice ID: {invoice_id})")
            
            # Send the invoice
            send_url = f"{invoice_url}/{invoice_id}/send"
            logger.info(f"Sending invoice to customer using endpoint: {send_url}")
            
            send_response = requests.post(
                send_url,
                headers=headers
            )
            logger.info(f"PayPal send invoice response status: {send_response.status_code}")
            
            # Log send response content for debugging
            try:
                send_response_content = send_response.json() if send_response.text else {}
                logger.debug(f"PayPal send invoice response: {json.dumps(send_response_content, indent=2)}")
            except ValueError:
                logger.debug(f"PayPal send invoice response (non-JSON): {send_response.text}")
            
            # Check for error responses on send
            if send_response.status_code >= 400:
                logger.error(f"PayPal send invoice error: HTTP {send_response.status_code} - {send_response.text}")
            
            send_response.raise_for_status()
            logger.info("Invoice successfully sent to customer")

            # Generate final payment URL
            payment_url = f"https://www.paypal.com/invoice/p/#{payment_url_id}"
            logger.info(f"Generated customer payment URL: {payment_url}")

            # Prepare result data
            result = {
                "invoice_id": invoice_id,
                "status": "SENT",
                "invoice_number": invoice_id,
                "payment_url": payment_url
            }
            logger.info(f"PayPal invoice creation completed successfully: {result}")
            
            # Final verification of payment URL
            if not result["payment_url"]:
                logger.error("Payment URL is empty in final result, this will cause issues in the application")
            
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"PayPal API request error: {str(e)}")
            logger.error(f"Response status: {getattr(e.response, 'status_code', 'Unknown status code')}")
            logger.error(f"Response text: {getattr(e.response, 'text', 'No response text')}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PayPal invoice creation: {str(e)}", exc_info=True)
            raise