# 📷 Step 5: File Upload

**Waktu:** 4-6 jam  
**Prerequisite:** Step 4 selesai

---

## 🎯 Tujuan

- Upload product images
- Image validation (size, type)
- Image processing (resize, thumbnail)
- AWS S3 storage untuk production
- Presigned URLs untuk frontend upload

---

## 📋 Tasks

### 5.1 Local Storage (Development)

**Di `settings/development.py`:**

```python
# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**Di `config/urls.py` (development only):**

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 5.2 Image Validation

**Buat `apps/core/validators.py`:**

```python
from django.core.exceptions import ValidationError
from PIL import Image
import os

def validate_image_file(file):
    """Validate image file"""
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(f"File size must not exceed 5MB")
    
    # Check extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Use: {', '.join(valid_extensions)}")
    
    # Verify it's a valid image
    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Invalid image file")


def validate_image_dimensions(file, min_width=100, min_height=100, max_width=4000, max_height=4000):
    """Validate image dimensions"""
    img = Image.open(file)
    width, height = img.size
    
    if width < min_width or height < min_height:
        raise ValidationError(f"Image must be at least {min_width}x{min_height} pixels")
    
    if width > max_width or height > max_height:
        raise ValidationError(f"Image must not exceed {max_width}x{max_height} pixels")
```

### 5.3 Image Processing Service

**Buat `apps/products/services/image_service.py`:**

```python
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class ImageService:
    
    @staticmethod
    def process_image(image_file, sizes=None):
        """
        Process uploaded image:
        - Convert to RGB (for JPEG)
        - Create multiple sizes
        - Return dict of processed images
        """
        if sizes is None:
            sizes = {
                'original': None,
                'large': (1200, 1200),
                'medium': (600, 600),
                'thumbnail': (150, 150),
            }
        
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        results = {}
        
        for name, size in sizes.items():
            if size is None:
                # Keep original
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                results[name] = ContentFile(buffer.getvalue())
            else:
                # Resize
                resized = img.copy()
                resized.thumbnail(size, Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                resized.save(buffer, format='JPEG', quality=85)
                results[name] = ContentFile(buffer.getvalue())
        
        return results
    
    @staticmethod
    def generate_filename(product_id, original_name, suffix=''):
        """Generate unique filename"""
        import uuid
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ['.jpg', '.jpeg']:
            ext = '.jpg'  # Always save as JPEG
        
        unique = uuid.uuid4().hex[:8]
        if suffix:
            return f"products/{product_id}/{unique}_{suffix}{ext}"
        return f"products/{product_id}/{unique}{ext}"
```

### 5.4 AWS S3 Configuration (Production)

**Install:**
```bash
pip install boto3 django-storages
```

**Di `settings/production.py`:**

```python
# AWS S3 Configuration
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_BUCKET')
AWS_S3_REGION_NAME = env('AWS_REGION', default='ap-southeast-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # Use bucket's ACL
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_QUERYSTRING_AUTH = True  # Use presigned URLs
AWS_QUERYSTRING_EXPIRE = 3600  # 1 hour

# Use S3 for media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

**Referensi:** [FILE_UPLOAD.md](../../../docs/04-advanced/FILE_UPLOAD.md) - S3 section

### 5.5 Upload Views

```python
class ProductImageUploadView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]
    
    def post(self, request, product_id):
        """Upload product image"""
        product = get_object_or_404(Product, pk=product_id)
        
        if 'image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=400)
        
        image_file = request.FILES['image']
        
        # Validate
        try:
            validate_image_file(image_file)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
        # Process image
        processed = ImageService.process_image(image_file)
        
        # Save to ProductImage
        # Determine if this is primary
        is_primary = not product.images.exists()
        
        product_image = ProductImage.objects.create(
            product=product,
            is_primary=is_primary,
            alt_text=request.data.get('alt_text', product.name)
        )
        
        # Save processed image (will use S3 in production)
        filename = ImageService.generate_filename(product_id, image_file.name)
        product_image.image.save(filename, processed['large'])
        
        # Optional: Save thumbnail separately
        # thumbnail_filename = ImageService.generate_filename(product_id, image_file.name, 'thumb')
        # product_image.thumbnail.save(thumbnail_filename, processed['thumbnail'])
        
        return Response(ProductImageSerializer(product_image).data, status=201)
    
    def delete(self, request, product_id, image_id):
        """Delete product image"""
        product = get_object_or_404(Product, pk=product_id)
        image = get_object_or_404(ProductImage, pk=image_id, product=product)
        
        # Delete file from storage
        image.image.delete()
        image.delete()
        
        # If deleted image was primary, set next image as primary
        if image.is_primary:
            next_image = product.images.first()
            if next_image:
                next_image.is_primary = True
                next_image.save()
        
        return Response(status=204)


class PresignedUploadURLView(APIView):
    """Get presigned URL for direct S3 upload"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Generate presigned URL for frontend upload"""
        filename = request.data.get('filename')
        content_type = request.data.get('content_type', 'image/jpeg')
        product_id = request.data.get('product_id')
        
        if not filename or not product_id:
            return Response({'error': 'filename and product_id required'}, status=400)
        
        # Generate S3 key
        key = ImageService.generate_filename(product_id, filename)
        
        # Generate presigned URL
        import boto3
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': key,
                'ContentType': content_type
            },
            ExpiresIn=3600
        )
        
        return Response({
            'upload_url': presigned_url,
            'key': key,
            'expires_in': 3600
        })
```

### 5.6 Background Processing dengan Celery

**Di `apps/products/tasks.py`:**

```python
from celery import shared_task
from .services.image_service import ImageService

@shared_task
def process_product_image(image_id):
    """Process image in background"""
    from .models import ProductImage
    
    image = ProductImage.objects.get(pk=image_id)
    
    # Download from S3 if needed
    # Process
    # Upload thumbnails back to S3
    
    # Update record with thumbnail URLs
    pass
```

**Referensi:** [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md)

---

## 🗂️ API Endpoints

```
POST   /api/admin/products/{id}/images/              # Upload image
DELETE /api/admin/products/{id}/images/{image_id}/   # Delete image
POST   /api/admin/products/{id}/images/reorder/      # Reorder images
PUT    /api/admin/products/{id}/images/{id}/primary/ # Set primary

# Presigned URLs (for frontend direct upload)
POST   /api/admin/upload/presigned-url/              # Get presigned URL
POST   /api/admin/upload/confirm/                    # Confirm upload complete
```

---

## ✅ Checklist

- [ ] Image validation (size, type, dimensions)
- [ ] Image processing service
- [ ] Multiple sizes (original, large, thumbnail)
- [ ] Local storage for development
- [ ] S3 storage for production
- [ ] Upload endpoint
- [ ] Delete endpoint
- [ ] Primary image logic
- [ ] Presigned URLs untuk direct upload
- [ ] Celery task untuk async processing

---

## 🔗 Referensi

- [FILE_UPLOAD.md](../../../docs/04-advanced/FILE_UPLOAD.md) - Complete guide
- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Celery

---

## ➡️ Next Step

Lanjut ke [06-EMAIL_NOTIFICATION.md](06-EMAIL_NOTIFICATION.md) - Order Emails
