import firebase_admin
from firebase_admin import credentials, firestore, storage
from PIL import Image
import io
import tempfile
from datetime import datetime
import logging
import os

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
            download_url = blob.generate_signed_url(
                expiration=datetime.now().timestamp() + 3600
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

    async def create_product_preview(self, user_id: str, product_image: Image.Image, 
                                   design: Image.Image, placement: str):
        """
        Create preview of product with design placed according to specified position
        
        Args:
            user_id: User identifier
            product_image: PIL Image of the product
            design: PIL Image of the design
            placement: One of 'leftChest', 'fullFront', 'centerChest', 'centerBack'
        """
        try:
            # Create preview
            preview = product_image.copy()
            
            # Get placement coordinates based on position
            position = self._get_placement_coordinates(placement, preview.size, design.size)
            if position:
                # Resize design based on placement
                design_size = self._get_design_size(placement, preview.size)
                resized_design = design.resize(design_size, Image.Resampling.LANCZOS)
                
                # Paste design onto product
                preview.paste(resized_design, position, resized_design)
                
                # Save preview
                preview_filename = f"preview_{placement}_{int(datetime.now().timestamp())}.png"
                storage_path = f'designs/user_{user_id}/previews/{preview_filename}'
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    preview.save(temp_file, format='PNG')
                    temp_file_path = temp_file.name

                # Upload to Firebase Storage
                blob = self.bucket.blob(storage_path)
                blob.upload_from_filename(temp_file_path)
                
                # Get download URL
                download_url = blob.generate_signed_url(
                    expiration=datetime.now().timestamp() + 3600
                )
                
                # Clean up
                os.unlink(temp_file_path)
                
                return {
                    'preview_url': download_url,
                    'storage_path': storage_path
                }
            
            raise ValueError(f"Invalid placement: {placement}")
            
        except Exception as e:
            logger.error(f"Error creating product preview: {str(e)}")
            raise

    def _get_placement_coordinates(self, placement: str, product_size: tuple, 
                                 design_size: tuple) -> tuple:
        """Get coordinates for design placement based on position"""
        product_w, product_h = product_size
        design_w, design_h = design_size
        
        placements = {
            'leftChest': (int(product_w * 0.64 - design_w/2),
                         int(product_h * 0.30 - design_h/2)),
            'fullFront': (int(product_w * 0.50 - design_w/2),
                         int(product_h * 0.35 - design_h/2)),
            'centerChest': (int(product_w * 0.50 - design_w/2),
                          int(product_h * 0.32 - design_h/2)),
            'centerBack': (int(product_w * 0.50 - design_w/2),
                         int(product_h * 0.25 - design_h/2))
        }
        
        return placements.get(placement)

    def _get_design_size(self, placement: str, product_size: tuple) -> tuple:
        """Get appropriate design size based on placement and product size"""
        product_w, _ = product_size
        
        sizes = {
            'leftChest': (int(product_w * 0.18), int(product_w * 0.18)),  # 90px equivalent
            'fullFront': (int(product_w * 0.40), int(product_w * 0.40)),  # 200px equivalent
            'centerChest': (int(product_w * 0.31), int(product_w * 0.31)),  # 154px equivalent
            'centerBack': (int(product_w * 0.36), int(product_w * 0.36))   # 180px equivalent
        }
        
        return sizes.get(placement)