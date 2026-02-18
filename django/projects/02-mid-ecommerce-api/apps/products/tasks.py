"""
Celery tasks for products app.
"""

from celery import shared_task
from django.core.files.base import ContentFile
from .models import ProductImage
from .services.image_service import ImageService


@shared_task
def process_product_image_async(image_id):
    """
    Process product image in background.
    Can be used to generate thumbnails or additional sizes after upload.
    
    Args:
        image_id: ProductImage ID
    
    Returns:
        dict: Processing result
    """
    try:
        image = ProductImage.objects.get(pk=image_id)
        
        # Re-process image to generate additional sizes
        # This is useful if you want to generate thumbnails asynchronously
        processed = ImageService.process_image(image.image)
        
        # You could save thumbnail separately here
        # thumbnail_filename = ImageService.generate_filename(
        #     image.product.id, 
        #     image.image.name, 
        #     'thumb'
        # )
        # Save thumbnail to a separate field if you have one
        
        return {
            'success': True,
            'image_id': image_id,
            'message': 'Image processed successfully'
        }
    except ProductImage.DoesNotExist:
        return {
            'success': False,
            'error': f'ProductImage {image_id} not found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_unused_images():
    """
    Cleanup task to remove unused product images from storage.
    Can be run periodically via Celery Beat.
    """
    # Implementation: find images not linked to any product
    # and delete them from storage
    pass
