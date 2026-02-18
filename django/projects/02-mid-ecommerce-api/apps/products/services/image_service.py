"""
Image processing service for product images.
"""

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
import uuid


class ImageService:
    """Service for processing and managing product images."""
    
    DEFAULT_SIZES = {
        'original': None,  # Keep original
        'large': (1200, 1200),
        'medium': (600, 600),
        'thumbnail': (150, 150),
    }
    
    @staticmethod
    def process_image(image_file, sizes=None):
        """
        Process uploaded image:
        - Convert to RGB (for JPEG compatibility)
        - Create multiple sizes
        - Return dict of processed images
        
        Args:
            image_file: Uploaded file object
            sizes: Dict of {name: (width, height)} or None for original
        
        Returns:
            Dict of {name: ContentFile}
        """
        if sizes is None:
            sizes = ImageService.DEFAULT_SIZES
        
        # Open image
        img = Image.open(image_file)
        
        # Convert to RGB if necessary (RGBA, P modes don't work with JPEG)
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create white background for transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if 'A' in img.mode:
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                img = background
            else:
                img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        results = {}
        
        for name, size in sizes.items():
            if size is None:
                # Keep original size
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=90, optimize=True)
                results[name] = ContentFile(buffer.getvalue())
            else:
                # Resize maintaining aspect ratio
                resized = img.copy()
                resized.thumbnail(size, Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                resized.save(buffer, format='JPEG', quality=85, optimize=True)
                results[name] = ContentFile(buffer.getvalue())
        
        return results
    
    @staticmethod
    def generate_filename(product_id, original_name, suffix=''):
        """
        Generate unique filename for product image.
        
        Args:
            product_id: Product ID
            original_name: Original filename
            suffix: Optional suffix (e.g., 'thumb', 'large')
        
        Returns:
            String path like 'products/{id}/{uuid}_{suffix}.jpg'
        """
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ['.jpg', '.jpeg']:
            ext = '.jpg'  # Always save as JPEG
        
        unique = uuid.uuid4().hex[:8]
        
        if suffix:
            return f"products/{product_id}/{unique}_{suffix}{ext}"
        return f"products/{product_id}/{unique}{ext}"
    
    @staticmethod
    def delete_image_files(image_field):
        """
        Delete image file from storage.
        
        Args:
            image_field: ImageField instance
        """
        if image_field and hasattr(image_field, 'storage'):
            try:
                image_field.delete(save=False)
            except Exception:
                pass  # File might not exist
