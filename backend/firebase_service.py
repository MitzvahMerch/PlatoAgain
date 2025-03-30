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

    def save_order_state(self, user_id: str, order_state_dict: dict) -> bool:
        """
        Save order state to Firestore
        
        Args:
            user_id: User identifier
            order_state_dict: OrderState converted to dictionary
        
        Returns:
            bool: Success or failure
        """
        try:
            # Save to active_conversations collection
            self.db.collection('active_conversations').document(user_id).set({
                'order_state': order_state_dict,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            logger.info(f"Saved order state to Firestore for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving order state to Firestore: {str(e)}")
            return False
    
    def save_completed_order(self, user_id: str, order_state_dict: dict) -> bool:
        """
        Save completed order to designs collection
        
        Args:
            user_id: User identifier
            order_state_dict: OrderState converted to dictionary
        
        Returns:
            bool: Success or failure
        """
        try:
            # Save to designs collection
            self.db.collection('designs').document(user_id).set(
                order_state_dict, merge=True
            )
            
            logger.info(f"Saved completed order to designs collection for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving completed order to Firestore: {str(e)}")
            return False

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
            
            # Get direct reference to the document using user_id
            design_ref = self.db.collection('designs').document(user_id)
            
            # Simplified structure - directly use the customer_info fields
            # with minimal transformation to reduce potential bugs
            update_data = {}
            
            # Customer data fields
            customer_fields = ['name', 'address', 'email']
            if any(field in customer_info for field in customer_fields):
                customer_data = {
                    'customerInfo': {
                        'name': customer_info.get('name'),
                        'address': customer_info.get('address'),
                        'email': customer_info.get('email'),
                        'updatedAt': firestore.SERVER_TIMESTAMP
                    }
                }
                update_data.update(customer_data)
            
            # Payment data fields
            payment_fields = ['invoice_id', 'invoice_number', 'status', 'payment_url']
            if any(field in customer_info for field in payment_fields):
                payment_data = {
                    'paymentInfo': {
                        'invoiceId': customer_info.get('invoice_id'),
                        'invoiceNumber': customer_info.get('invoice_number'),
                        'status': customer_info.get('status'),
                        'paymentUrl': customer_info.get('payment_url')
                    }
                }
                update_data.update(payment_data)
            
            # Update the document if we have data to update
            if update_data:
                design_ref.update(update_data)
                logger.info(f"Successfully updated customer info for user {user_id}")
                return True
            else:
                logger.warning(f"No data to update for user {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating customer info for user {user_id}: {str(e)}")
            return False

    async def upload_design(self, user_id: str, design_file, filename: str):
        """
        Upload design to Firebase Storage and store metadata in Firestore
        
        Args:
            user_id: User identifier (e.g., user_xrmydiaiz)
            design_file: PIL Image or file-like object
            filename: Original filename of the design
        """
        try:
            logger.info(f"Starting design upload for user {user_id}")
            
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
            storage_path = f'designs/{user_id}/{filename}'
            logger.info(f"Storage path for design: {storage_path}")
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(storage_path)
            blob.upload_from_filename(temp_file_path)
            logger.info("Design uploaded to Firebase Storage successfully")
            
            # Get download URL
            expiration_time = int(datetime.now().timestamp() + 3600)
            download_url = blob.generate_signed_url(
                expiration=expiration_time
            )
            logger.info(f"Generated download URL: {download_url}")
            
            # Store metadata in Firestore using user_id as document ID
            design_ref = self.db.collection('designs').document(user_id)
            design_data = {
                'downloadURL': download_url,
                'fileName': filename,
                'fileSize': os.path.getsize(temp_file_path),
                'fileType': 'image/png',
                'status': 'pending_review',
                'uploadDate': firestore.SERVER_TIMESTAMP,
                'userId': user_id,
                'designPath': download_url  # Add this field for consistency with OrderState
            }
            
            # Use set with merge=True to update or create the document
            logger.info(f"Attempting to store metadata in Firestore for user {user_id}")
            design_ref.set(design_data, merge=True)
            logger.info("Design metadata stored in Firestore successfully")
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return {
                'storage_path': storage_path,
                'download_url': download_url,
                'design_id': user_id
            }
            
        except Exception as e:
            logger.error(f"Error uploading design: {str(e)}")
            raise
    
    def load_order_state(self, user_id: str) -> dict:
        """
        Load order state from Firestore
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Order state dictionary or empty dict if not found
        """
        try:
            # Try active_conversations first
            doc_ref = self.db.collection('active_conversations').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists and 'order_state' in doc.to_dict():
                logger.info(f"Loaded order state from active_conversations for user {user_id}")
                return doc.to_dict().get('order_state', {})
            
            # If not found, try designs collection
            doc_ref = self.db.collection('designs').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                logger.info(f"Loaded order state from designs collection for user {user_id}")
                return doc.to_dict()
            
            logger.info(f"No order state found for user {user_id}")
            return {}
            
        except Exception as e:
            logger.error(f"Error loading order state from Firestore: {str(e)}")
            return {}