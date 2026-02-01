# 📁 FILE UPLOAD - Django (Junior → Senior)

Dokumentasi lengkap tentang file upload di Django, dari local storage hingga cloud storage (S3).

---

## 🎯 Kenapa File Upload Penting?

```
Use Cases:
✅ Profile pictures
✅ Document uploads (PDF, contracts)
✅ Image galleries
✅ CSV/Excel imports
✅ Attachments in messages
```

---

## 1️⃣ JUNIOR LEVEL - Basic File Upload

### Model dengan FileField

```python
# apps/users/models.py
from django.db import models
import os

def user_avatar_path(instance, filename):
    """
    Generate path: avatars/user_123/filename.jpg
    """
    ext = filename.split('.')[-1]
    filename = f'avatar.{ext}'
    return os.path.join('avatars', f'user_{instance.id}', filename)


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    
    # Basic file field
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True
    )
    
    # Document field
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',  # resumes/2024/01/file.pdf
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"Profile of {self.user.username}"
```

### Settings Configuration

```python
# config/settings/base.py
import os

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
```

### URL Configuration (Development)

```python
# config/urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your urls
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Basic Serializer

```python
# apps/users/serializers.py
from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'avatar', 'avatar_url', 'resume']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.avatar.url)
        return None
```

### Basic View

```python
# apps/users/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UserProfile
from .serializers import UserProfileSerializer

class AvatarUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        profile = request.user.profile
        
        if 'avatar' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        serializer = UserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
```

---

## 2️⃣ MID LEVEL - File Validation

### Comprehensive Validators

```python
# apps/core/validators.py
from django.core.exceptions import ValidationError
import os

def validate_file_size(value, max_size_mb=5):
    """
    Validate file size
    """
    max_size = max_size_mb * 1024 * 1024  # Convert to bytes
    
    if value.size > max_size:
        raise ValidationError(f'File size must be less than {max_size_mb}MB')


def validate_file_extension(value, allowed_extensions):
    """
    Validate file extension
    """
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type not allowed. Allowed: {", ".join(allowed_extensions)}'
        )


def validate_image(value):
    """
    Validate image file
    """
    allowed = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    validate_file_extension(value, allowed)
    validate_file_size(value, max_size_mb=5)


def validate_document(value):
    """
    Validate document file
    """
    allowed = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
    validate_file_extension(value, allowed)
    validate_file_size(value, max_size_mb=10)


def validate_image_dimensions(value, max_width=2000, max_height=2000):
    """
    Validate image dimensions
    """
    from PIL import Image
    
    img = Image.open(value)
    width, height = img.size
    
    if width > max_width or height > max_height:
        raise ValidationError(
            f'Image dimensions must be at most {max_width}x{max_height}px'
        )
```

### Model dengan Validators

```python
# apps/users/models.py
from django.db import models
from apps.core.validators import validate_image, validate_document

class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    
    avatar = models.ImageField(
        upload_to='avatars/',
        validators=[validate_image],
        null=True,
        blank=True
    )
    
    resume = models.FileField(
        upload_to='resumes/',
        validators=[validate_document],
        null=True,
        blank=True
    )
```

### Serializer Validation

```python
# apps/users/serializers.py
from rest_framework import serializers
from PIL import Image
import os

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    # Configuration
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
    MAX_SIZE_MB = 5
    
    def validate_file(self, value):
        # Check extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'File type {ext} not allowed. Allowed: {self.ALLOWED_EXTENSIONS}'
            )
        
        # Check size
        max_size = self.MAX_SIZE_MB * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be less than {self.MAX_SIZE_MB}MB'
            )
        
        # Check if image is valid (for image files)
        if ext in ['.jpg', '.jpeg', '.png']:
            try:
                img = Image.open(value)
                img.verify()
            except Exception:
                raise serializers.ValidationError('Invalid image file')
        
        return value
```

### File Upload Service

```python
# apps/core/services/file_service.py
import os
import uuid
from django.conf import settings
from PIL import Image


class FileService:
    """
    Service untuk handle file operations
    """
    
    @staticmethod
    def generate_filename(original_filename: str, prefix: str = '') -> str:
        """
        Generate unique filename
        """
        ext = os.path.splitext(original_filename)[1].lower()
        unique_id = uuid.uuid4().hex[:8]
        
        if prefix:
            return f'{prefix}_{unique_id}{ext}'
        return f'{unique_id}{ext}'
    
    @staticmethod
    def resize_image(image_path: str, max_width: int = 800, max_height: int = 800) -> str:
        """
        Resize image if too large
        """
        img = Image.open(image_path)
        
        # Only resize if larger than max dimensions
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
        
        return image_path
    
    @staticmethod
    def create_thumbnail(image_path: str, size: tuple = (150, 150)) -> str:
        """
        Create thumbnail from image
        """
        img = Image.open(image_path)
        img.thumbnail(size, Image.LANCZOS)
        
        # Generate thumbnail path
        base, ext = os.path.splitext(image_path)
        thumb_path = f'{base}_thumb{ext}'
        
        img.save(thumb_path, optimize=True, quality=85)
        return thumb_path
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete file from storage
        """
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
```

---

## 3️⃣ MID-SENIOR LEVEL - Multiple File Upload

### Multiple Files Model

```python
# apps/documents/models.py
from django.db import models

class Document(models.Model):
    """
    Document with multiple attachments
    """
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Attachment(models.Model):
    """
    File attachment (one-to-many)
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
```

### Multiple Files Serializer

```python
# apps/documents/serializers.py
from rest_framework import serializers
from .models import Document, Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'filename', 'file_size', 'content_type', 'url', 'uploaded_at']
    
    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url)


class DocumentSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'attachments', 'files', 'created_at']
    
    def create(self, validated_data):
        files = validated_data.pop('files', [])
        document = Document.objects.create(**validated_data)
        
        for file in files:
            Attachment.objects.create(
                document=document,
                file=file,
                content_type=file.content_type
            )
        
        return document
```

### Multiple Files View

```python
# apps/documents/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document, Attachment
from .serializers import DocumentSerializer, AttachmentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.prefetch_related('attachments')
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=True, methods=['post'])
    def upload_files(self, request, pk=None):
        """
        Upload multiple files to existing document
        POST /api/documents/{id}/upload_files/
        """
        document = self.get_object()
        files = request.FILES.getlist('files')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attachments = []
        for file in files:
            attachment = Attachment.objects.create(
                document=document,
                file=file,
                content_type=file.content_type
            )
            attachments.append(attachment)
        
        serializer = AttachmentSerializer(
            attachments,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='attachments/(?P<attachment_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attachment_id=None):
        """
        Delete specific attachment
        DELETE /api/documents/{id}/attachments/{attachment_id}/
        """
        document = self.get_object()
        
        try:
            attachment = document.attachments.get(id=attachment_id)
            attachment.file.delete()  # Delete file from storage
            attachment.delete()  # Delete database record
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Attachment.DoesNotExist:
            return Response(
                {'error': 'Attachment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
```

---

## 4️⃣ SENIOR LEVEL - AWS S3 Storage

### Install boto3

```bash
pip install boto3 django-storages
```

### S3 Configuration

```python
# config/settings/production.py
import os

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-1')

# S3 Settings
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day cache
}
AWS_DEFAULT_ACL = 'private'  # Private by default
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True  # Generate signed URLs
AWS_QUERYSTRING_EXPIRE = 3600  # URL expires in 1 hour

# Static files (optional - if using S3 for static)
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### Custom S3 Storage Backend

```python
# apps/core/storage.py
from storages.backends.s3boto3 import S3Boto3Storage

class PublicMediaStorage(S3Boto3Storage):
    """
    Storage for public files (avatars, etc.)
    """
    location = 'media/public'
    default_acl = 'public-read'
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """
    Storage for private files (documents, resumes)
    """
    location = 'media/private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False  # Use signed URLs
```

### Model dengan Custom Storage

```python
# apps/users/models.py
from django.db import models
from django.conf import settings

# Choose storage based on environment
if settings.DEBUG:
    from django.core.files.storage import FileSystemStorage
    public_storage = FileSystemStorage()
    private_storage = FileSystemStorage()
else:
    from apps.core.storage import PublicMediaStorage, PrivateMediaStorage
    public_storage = PublicMediaStorage()
    private_storage = PrivateMediaStorage()


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    
    # Public file (avatar - accessible by anyone)
    avatar = models.ImageField(
        upload_to='avatars/',
        storage=public_storage,
        null=True,
        blank=True
    )
    
    # Private file (resume - needs signed URL)
    resume = models.FileField(
        upload_to='resumes/',
        storage=private_storage,
        null=True,
        blank=True
    )
```

### Generate Signed URL

```python
# apps/core/services/s3_service.py
import boto3
from botocore.exceptions import ClientError
from django.conf import settings


class S3Service:
    """
    Service untuk S3 operations
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate signed URL for private file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f'Error generating signed URL: {e}')
    
    def generate_presigned_upload_url(
        self,
        object_key: str,
        content_type: str,
        expiration: int = 3600
    ) -> dict:
        """
        Generate signed URL for direct upload from frontend
        """
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=object_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 10 * 1024 * 1024]  # Max 10MB
                ],
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            raise Exception(f'Error generating upload URL: {e}')
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from S3
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=object_key
            )
            return True
        except ClientError:
            return False
```

### View untuk Signed URL

```python
# apps/documents/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.services.s3_service import S3Service

class PresignedUploadView(APIView):
    """
    Generate presigned URL for direct upload to S3
    """
    
    def post(self, request):
        """
        POST /api/upload/presigned/
        Body: { "filename": "document.pdf", "content_type": "application/pdf" }
        """
        filename = request.data.get('filename')
        content_type = request.data.get('content_type')
        
        if not filename or not content_type:
            return Response(
                {'error': 'filename and content_type required'},
                status=400
            )
        
        # Generate unique key
        import uuid
        object_key = f'uploads/{uuid.uuid4().hex}/{filename}'
        
        s3_service = S3Service()
        presigned_data = s3_service.generate_presigned_upload_url(
            object_key=object_key,
            content_type=content_type
        )
        
        return Response({
            'upload_url': presigned_data['url'],
            'fields': presigned_data['fields'],
            'object_key': object_key
        })


class PresignedDownloadView(APIView):
    """
    Generate presigned URL for downloading private file
    """
    
    def get(self, request, object_key):
        """
        GET /api/download/presigned/{object_key}/
        """
        s3_service = S3Service()
        
        try:
            url = s3_service.generate_presigned_url(object_key)
            return Response({'download_url': url})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

---

## 5️⃣ EXPERT LEVEL - Image Processing Pipeline

### Celery Task untuk Image Processing

```python
# apps/media/tasks.py
from celery import shared_task
from PIL import Image
import os
from django.conf import settings

@shared_task
def process_uploaded_image(image_path: str, user_id: int):
    """
    Background task untuk process uploaded image:
    1. Resize to max dimensions
    2. Create thumbnails
    3. Optimize for web
    """
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    
    if not os.path.exists(full_path):
        return {'error': 'File not found'}
    
    img = Image.open(full_path)
    base, ext = os.path.splitext(full_path)
    
    # 1. Resize original if too large
    max_size = (1920, 1080)
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(full_path, optimize=True, quality=85)
    
    # 2. Create medium thumbnail (400x400)
    img_medium = img.copy()
    img_medium.thumbnail((400, 400), Image.LANCZOS)
    medium_path = f'{base}_medium{ext}'
    img_medium.save(medium_path, optimize=True, quality=85)
    
    # 3. Create small thumbnail (150x150)
    img_thumb = img.copy()
    img_thumb.thumbnail((150, 150), Image.LANCZOS)
    thumb_path = f'{base}_thumb{ext}'
    img_thumb.save(thumb_path, optimize=True, quality=85)
    
    # Return paths relative to MEDIA_ROOT
    return {
        'original': image_path,
        'medium': os.path.relpath(medium_path, settings.MEDIA_ROOT),
        'thumbnail': os.path.relpath(thumb_path, settings.MEDIA_ROOT)
    }


@shared_task
def cleanup_orphan_files():
    """
    Scheduled task: cleanup files tanpa database reference
    Run daily via celery beat
    """
    from apps.users.models import UserProfile
    from apps.documents.models import Attachment
    
    # Get all referenced files
    referenced_files = set()
    
    for profile in UserProfile.objects.exclude(avatar=''):
        referenced_files.add(profile.avatar.name)
    
    for attachment in Attachment.objects.all():
        referenced_files.add(attachment.file.name)
    
    # Walk through media directory
    orphan_count = 0
    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
            
            if relative_path not in referenced_files:
                os.remove(file_path)
                orphan_count += 1
    
    return {'deleted': orphan_count}
```

### Signal untuk Auto-Processing

```python
# apps/media/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.users.models import UserProfile
from .tasks import process_uploaded_image

@receiver(post_save, sender=UserProfile)
def process_avatar_on_upload(sender, instance, **kwargs):
    """
    Auto-process avatar when uploaded
    """
    if instance.avatar:
        # Delay processing to background
        process_uploaded_image.delay(
            instance.avatar.name,
            instance.user_id
        )


@receiver(pre_delete, sender=UserProfile)
def delete_avatar_on_user_delete(sender, instance, **kwargs):
    """
    Delete avatar file when user profile deleted
    """
    if instance.avatar:
        instance.avatar.delete(save=False)
```

---

## 📋 Quick Reference

### File Upload Checklist

```
□ Validate file extension
□ Validate file size
□ Validate file content (not just extension)
□ Generate unique filename
□ Store securely (private by default)
□ Use signed URLs for private files
□ Process images in background
□ Create thumbnails for images
□ Cleanup orphan files periodically
□ Log all upload activities
```

### Common Content Types

```python
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
}
```

---

## 🔗 Related Docs

- [BACKGROUND_JOBS.md](BACKGROUND_JOBS.md) - Async image processing
- [SECURITY.md](../03-authentication/SECURITY.md) - File upload security
- [SIGNALS.md](SIGNALS.md) - Auto-processing signals
