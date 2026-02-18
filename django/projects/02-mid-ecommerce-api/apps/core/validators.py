"""
File and image validators.
"""

from django.core.exceptions import ValidationError
from PIL import Image
import os


def validate_image_file(file):
    """
    Validate image file type and size.
    Max size: 5MB
    Allowed: jpg, jpeg, png, webp
    """
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("File size must not exceed 5MB")
    
    # Check extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Use: {', '.join(valid_extensions)}")
    
    # Verify it's a valid image
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)  # Reset file pointer after verify
    except Exception:
        raise ValidationError("Invalid image file")


def validate_image_dimensions(file, min_width=100, min_height=100, max_width=4000, max_height=4000):
    """
    Validate image dimensions.
    Default: min 100x100, max 4000x4000
    """
    try:
        img = Image.open(file)
        width, height = img.size
        
        if width < min_width or height < min_height:
            raise ValidationError(f"Image must be at least {min_width}x{min_height} pixels")
        
        if width > max_width or height > max_height:
            raise ValidationError(f"Image must not exceed {max_width}x{max_height} pixels")
        
        file.seek(0)  # Reset file pointer
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError("Unable to read image dimensions")
