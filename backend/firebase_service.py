import firebase_admin
from firebase_admin import credentials, firestore, storage
from PIL import Image
import io
import tempfile
from datetime import datetime
import logging
import os
import urllib.parse
import requests

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        """Initialize Firebase with admin credentials"""
        try:
            cred = credentials.Certificate('./mitzvahmerch-ac346-firebase-adminsdk-ztyq5-7cb78575b3.json')
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'mitzvahmerch-ac346.appspot.com'
            })
            self.db = firestore.client()
            self.bucket = storage.bucket()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    def update_customer_info(self, user_id: str, customer_info: dict) -> bool:
        """
        Update customer information in Firestore using the user ID as document ID.
        
        Args:
            user_id: User identifier (matches document ID)
            customer_info: Dict containing extracted customer information
                {
                    'name': str (optional),
                    'address': str (optional),
                    'email': str (optional),
                    'invoice_id': str (optional),
                    'invoice_number': str (optional),
                    'status': str (optional),
                    'payment_url': str (optional)
                }
        """
        try:
            logger.info(f"Starting update_customer_info for user {user_id}")
            logger.info(f"Received customer_info: {customer_info}")
            
            # Get direct reference to the document using user_id
            design_ref = self.db.collection('designs').document(user_id)
            logger.info(f"Got Firestore reference for document: {user_id}")
            
            # Separate customer info and PayPal info
            customer_data = {
                'name': customer_info.get('name'),
                'address': customer_info.get('address'),
                'email': customer_info.get('email'),
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            logger.info(f"Created customer_data structure: {customer_data}")
            
            # Create PayPal data if present
            paypal_data = {}
            paypal_fields = ['invoice_id', 'invoice_number', 'status', 'payment_url']
            logger.info(f"PayPal fields to check: {paypal_fields}")
            logger.info(f"Keys present in customer_info: {customer_info.keys()}")
            
            # Log which PayPal fields are present
            for field in paypal_fields:
                logger.info(f"Checking field '{field}': {'present' if field in customer_info else 'absent'}")
            
            if any(field in customer_info for field in paypal_fields):
                logger.info("Found PayPal fields in customer_info, processing...")
                paypal_data = {}
                for field in paypal_fields:
                    if field in customer_info:
                        paypal_data[field] = customer_info[field]
                        logger.info(f"Added PayPal field {field} with value: {customer_info[field]}")
                    else:
                        logger.warning(f"PayPal field {field} not found in customer_info")
                
                logger.info(f"Final PayPal data structure: {paypal_data}")
            else:
                logger.info("No PayPal fields found in customer_info")
            
            # Prepare update data
            update_data = {}
            logger.info("Preparing final update_data structure")
            
            # Only include customerInfo if we have customer data
            if any(v for k, v in customer_data.items() if k != 'updatedAt'):
                update_data['customerInfo'] = customer_data
                logger.info(f"Added customerInfo to update_data: {customer_data}")
            else:
                logger.info("No customer data to add to update_data")
            
            # Add PayPal data if present
            if paypal_data:
                update_data['paypalInfo'] = paypal_data
                logger.info(f"Added paypalInfo to update_data: {paypal_data}")
            else:
                logger.info("No PayPal data to add to update_data")
            
            logger.info(f"Final update_data structure: {update_data}")

            # Update the document
            logger.info("Attempting Firestore update...")
            design_ref.update(update_data)
            logger.info(f"Successfully updated customer info for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating customer info for user {user_id}: {str(e)}")
            logger.error(f"Full customer_info that caused error: {customer_info}")
            if 'paypal_data' in locals():
                logger.error(f"PayPal data at time of error: {paypal_data}")
            if 'update_data' in locals():
                logger.error(f"Update data at time of error: {update_data}")
            raise

    async def upload_design(self, user_id: str, design_file, filename: str):
        """
        Upload design to Firebase Storage and store metadata in Firestore
        
        Args:
            user_id: User identifier (e.g., user_xrmydiaiz)
            design_file: PIL Image or file-like object
            filename: Original filename of the design
        """
        try:
            # Process design with Pillow
            if isinstance(design_file, Image.Image):
                img = design_file
            else:
                img = Image.open(design_file)
            
            # Convert to RGBA if needed for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create temporary file for processed image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                img.save(temp_file, format='PNG')
                temp_file_path = temp_file.name

            # Define storage path following your structure
            storage_path = f'designs/user_{user_id}/{filename}'
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(storage_path)
            blob.upload_from_filename(temp_file_path)
            
            # Get download URL
            expiration_time = int(datetime.now().timestamp() + 3600)
            download_url = blob.generate_signed_url(
                expiration=expiration_time
            )
            
            # Store metadata in Firestore using your existing structure
            design_ref = self.db.collection('designs').document()
            design_data = {
                'downloadURL': download_url,
                'fileName': filename,
                'fileSize': os.path.getsize(temp_file_path),
                'fileType': 'image/png',
                'status': 'pending_review',
                'uploadDate': firestore.SERVER_TIMESTAMP,
                'userId': f'user_{user_id}'
            }
            design_ref.set(design_data)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return {
                'storage_path': storage_path,
                'download_url': download_url,
                'design_id': design_ref.id
            }
            
        except Exception as e:
            logger.error(f"Error uploading design: {str(e)}")
            raise

    async def create_product_preview(self, user_id: str, product_image: str, 
                               design_url: str, placement: str):
        """
        Create preview of product with design placed according to specified position
        
        Args:
            user_id: User identifier
            product_image: Local path to the product image
            design_url: URL of the design in Firebase Storage
            placement: One of 'leftChest', 'fullFront', 'centerChest', 'centerBack'
        """
        try:
            # Download design from Firebase Storage
            try:
                # Extract path from HTTP URL properly
                path_start = design_url.find('/o/') + 3
                path_end = design_url.find('?')
                if path_start > 2 and path_end > path_start:
                    design_path = design_url[path_start:path_end]
                    design_path = urllib.parse.unquote(design_path)  # URL decode the path
                    logger.info(f"Extracted design path: {design_path}")
                else:
                    raise ValueError(f"Invalid design URL format: {design_url}")
                
                design_blob = self.bucket.blob(design_path)
                design_bytes = design_blob.download_as_bytes()
                design = Image.open(io.BytesIO(design_bytes)).convert('RGB')
                
            except Exception as e:
                logger.error(f"Error downloading design from Firebase: {str(e)}")
                raise ValueError(f"Unable to download design from URL: {design_url}")

            # Load product image from local path
            try:
                # Remove leading slash if present
                local_image_path = product_image.lstrip('/')
                preview = Image.open(local_image_path).convert('RGB')
            except Exception as e:
                logger.error(f"Error loading product image: {str(e)}")
                raise ValueError(f"Unable to load product image from path: {product_image}")
            
            # Define fixed sizes and positions
            positions = {
                'fullFront': {
                    'size': (200, 200),
                    'position': (500, 475)  # 50% left, 38% top
                },
                'centerChest': {
                    'size': (154, 154),
                    'position': (500, 437)  # 50% left, 35% top
                },
                'leftChest': {
                    'size': (90, 90),
                    'position': (640, 375)  # 64% left, 30% top
                },
                'centerBack': {
                    'size': (180, 180),
                    'position': (500, 350)  # 50% left, 28% top
                }
            }
            
            if placement in positions:
                specs = positions[placement]
                
                # Resize logo
                resized_design = design.resize(specs['size'])
                
                # Mirror the logo horizontally for left chest placement
                if placement == 'leftChest':
                    resized_design = resized_design.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                
                # Simple paste
                preview.paste(resized_design, specs['position'])
                
                # Create previews directory if it doesn't exist
                preview_dir = f'productimages/previews/{user_id}'
                os.makedirs(preview_dir, exist_ok=True)
                
                # Save preview image
                preview_filename = f"preview_{placement}_{int(datetime.now().timestamp())}.png"
                preview_path = f"{preview_dir}/{preview_filename}"
                preview.save(preview_path, format="PNG")
                
                # Return the relative path that matches our product image format
                return {
                    'preview_url': f"/productimages/previews/{user_id}/{preview_filename}"
                }
            
            raise ValueError(f"Invalid placement: {placement}")
            
        except Exception as e:
            logger.error(f"Error creating product preview: {str(e)}")
            raise