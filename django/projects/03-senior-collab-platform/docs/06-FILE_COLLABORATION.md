# 📁 Step 6: File Collaboration

**Waktu:** 4-6 jam  
**Prerequisite:** Step 5 selesai

---

## 🎯 Tujuan

- Shared file storage dengan S3
- File versioning
- Presigned URLs untuk upload/download
- File preview
- Access control per workspace

---

## 📋 Tasks

### 6.1 File Model

**Di `apps/files/models.py`:**

```python
from django.db import models
from apps.core.models import BaseModel, SoftDeleteModel
from django.conf import settings
import mimetypes

class File(SoftDeleteModel):
    """Workspace shared file"""
    
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='files'
    )
    
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file_key = models.CharField(max_length=500, unique=True)  # S3 key
    
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    
    # Organization
    folder = models.ForeignKey(
        'Folder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files'
    )
    
    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files'
    )
    
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    
    # Image specific
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'folder']),
            models.Index(fields=['workspace', 'mime_type']),
        ]
    
    @property
    def extension(self):
        return self.name.rsplit('.', 1)[-1] if '.' in self.name else ''
    
    @property
    def is_image(self):
        return self.mime_type.startswith('image/')
    
    @property
    def is_document(self):
        document_types = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument']
        return any(self.mime_type.startswith(t) for t in document_types)


class FileVersion(BaseModel):
    """File version history"""
    
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version = models.IntegerField()
    file_key = models.CharField(max_length=500)
    size = models.BigIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    comment = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['file', 'version']
        ordering = ['-version']


class Folder(BaseModel):
    """Folder structure"""
    
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='folders'
    )
    
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        unique_together = ['workspace', 'parent', 'name']
        ordering = ['name']
    
    @property
    def path(self):
        """Get full folder path"""
        parts = [self.name]
        current = self.parent
        
        while current:
            parts.insert(0, current.name)
            current = current.parent
        
        return '/'.join(parts)
```

### 6.2 File Service

**Buat `apps/files/services.py`:**

```python
import boto3
from botocore.config import Config
from django.conf import settings
import uuid
import mimetypes
from PIL import Image
from io import BytesIO

class S3Service:
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    def generate_upload_url(self, workspace_id, filename, content_type):
        """Generate presigned URL for direct upload"""
        key = f'workspaces/{workspace_id}/files/{uuid.uuid4()}/{filename}'
        
        url = self.client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket,
                'Key': key,
                'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return {
            'upload_url': url,
            'file_key': key
        }
    
    def generate_download_url(self, file_key, filename, expires=3600):
        """Generate presigned URL for download"""
        return self.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': file_key,
                'ResponseContentDisposition': f'attachment; filename="{filename}"'
            },
            ExpiresIn=expires
        )
    
    def generate_view_url(self, file_key, expires=3600):
        """Generate presigned URL for viewing (inline)"""
        return self.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': file_key
            },
            ExpiresIn=expires
        )
    
    def delete_file(self, file_key):
        """Delete file from S3"""
        self.client.delete_object(Bucket=self.bucket, Key=file_key)
    
    def copy_file(self, source_key, dest_key):
        """Copy file within S3"""
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={'Bucket': self.bucket, 'Key': source_key},
            Key=dest_key
        )


class FileService:
    
    @classmethod
    def create_file(cls, workspace, file_key, filename, size, mime_type, user, folder=None):
        """Create file record after upload"""
        from .models import File
        
        file = File.objects.create(
            workspace=workspace,
            name=filename,
            original_name=filename,
            file_key=file_key,
            size=size,
            mime_type=mime_type,
            uploaded_by=user,
            folder=folder
        )
        
        # Process if image
        if file.is_image:
            cls.process_image(file)
        
        # Log activity
        from apps.activity.tasks import log_activity
        log_activity.delay(
            workspace_id=str(workspace.id),
            user_id=str(user.id),
            action='upload',
            target_type='file',
            target_id=str(file.id),
            metadata={'filename': filename}
        )
        
        return file
    
    @classmethod
    def process_image(cls, file):
        """Extract image metadata"""
        # Download image to get dimensions
        s3 = S3Service()
        response = s3.client.get_object(Bucket=s3.bucket, Key=file.file_key)
        
        img = Image.open(BytesIO(response['Body'].read()))
        file.width = img.width
        file.height = img.height
        file.save()
    
    @classmethod
    def create_version(cls, file, new_key, size, user, comment=''):
        """Create new version of file"""
        from .models import FileVersion
        
        # Get next version number
        last_version = file.versions.first()
        new_version = (last_version.version + 1) if last_version else 1
        
        # Save current as version
        FileVersion.objects.create(
            file=file,
            version=new_version,
            file_key=file.file_key,
            size=file.size,
            created_by=user,
            comment=comment
        )
        
        # Update file with new content
        file.file_key = new_key
        file.size = size
        file.save()
        
        return file
    
    @classmethod
    def restore_version(cls, file, version, user):
        """Restore file to previous version"""
        from .models import FileVersion
        
        version_obj = file.versions.get(version=version)
        
        # Copy old version to new key
        s3 = S3Service()
        new_key = f'workspaces/{file.workspace_id}/files/{uuid.uuid4()}/{file.name}'
        s3.copy_file(version_obj.file_key, new_key)
        
        # Create version for current
        cls.create_version(file, new_key, version_obj.size, user, f'Restored from v{version}')
        
        return file


class UploadService:
    """Handle multipart uploads for large files"""
    
    @classmethod
    def initiate_multipart(cls, workspace_id, filename, content_type):
        """Start multipart upload"""
        s3 = S3Service()
        key = f'workspaces/{workspace_id}/files/{uuid.uuid4()}/{filename}'
        
        response = s3.client.create_multipart_upload(
            Bucket=s3.bucket,
            Key=key,
            ContentType=content_type
        )
        
        return {
            'upload_id': response['UploadId'],
            'file_key': key
        }
    
    @classmethod
    def get_part_url(cls, file_key, upload_id, part_number):
        """Get presigned URL for uploading a part"""
        s3 = S3Service()
        
        return s3.client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': s3.bucket,
                'Key': file_key,
                'UploadId': upload_id,
                'PartNumber': part_number
            },
            ExpiresIn=3600
        )
    
    @classmethod
    def complete_multipart(cls, file_key, upload_id, parts):
        """Complete multipart upload"""
        s3 = S3Service()
        
        s3.client.complete_multipart_upload(
            Bucket=s3.bucket,
            Key=file_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
```

**Referensi:** [FILE_UPLOAD.md](../../../docs/04-advanced/FILE_UPLOAD.md)

### 6.3 Views

```python
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

class FileListView(generics.ListCreateAPIView):
    serializer_class = FileSerializer
    permission_classes = [IsWorkspaceMember]
    
    def get_queryset(self):
        workspace = self.get_workspace()
        folder_id = self.request.query_params.get('folder')
        
        qs = File.objects.filter(workspace=workspace)
        if folder_id:
            qs = qs.filter(folder_id=folder_id)
        else:
            qs = qs.filter(folder__isnull=True)
        
        return qs.select_related('uploaded_by', 'folder')


class UploadURLView(APIView):
    """Get presigned URL for file upload"""
    permission_classes = [IsWorkspaceMember]
    
    def post(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        filename = request.data.get('filename')
        content_type = request.data.get('content_type')
        
        s3 = S3Service()
        result = s3.generate_upload_url(workspace.id, filename, content_type)
        
        return Response(result)


class ConfirmUploadView(APIView):
    """Confirm file upload after S3 direct upload"""
    permission_classes = [IsWorkspaceMember]
    
    def post(self, request, workspace_slug):
        workspace = get_object_or_404(Workspace, slug=workspace_slug)
        
        file = FileService.create_file(
            workspace=workspace,
            file_key=request.data['file_key'],
            filename=request.data['filename'],
            size=request.data['size'],
            mime_type=request.data['content_type'],
            user=request.user,
            folder_id=request.data.get('folder_id')
        )
        
        return Response(FileSerializer(file).data)


class DownloadURLView(APIView):
    """Get presigned URL for download"""
    permission_classes = [IsWorkspaceMember]
    
    def get(self, request, file_id):
        file = get_object_or_404(File, id=file_id)
        
        s3 = S3Service()
        url = s3.generate_download_url(file.file_key, file.name)
        
        return Response({'download_url': url})


class FileVersionsView(generics.ListAPIView):
    serializer_class = FileVersionSerializer
    
    def get_queryset(self):
        file = get_object_or_404(File, id=self.kwargs['file_id'])
        return file.versions.select_related('created_by')


class RestoreVersionView(APIView):
    def post(self, request, file_id, version):
        file = get_object_or_404(File, id=file_id)
        
        FileService.restore_version(file, version, request.user)
        
        return Response(FileSerializer(file).data)
```

---

## 📡 Upload Flow

```
1. Client -> GET /api/files/upload-url/
   <- {upload_url, file_key}

2. Client -> PUT upload_url (direct to S3)
   <- 200 OK

3. Client -> POST /api/files/confirm-upload/
   <- File object
```

---

## ✅ Checklist

- [ ] File model dengan S3 key
- [ ] FileVersion model
- [ ] Folder model
- [ ] S3Service dengan presigned URLs
- [ ] FileService untuk CRUD
- [ ] UploadService untuk multipart
- [ ] Version management
- [ ] Image metadata extraction
- [ ] Upload/download API endpoints
- [ ] Folder structure API

---

## 🔗 Referensi

- [FILE_UPLOAD.md](../../../docs/04-advanced/FILE_UPLOAD.md) - Complete guide

---

## ➡️ Next Step

Lanjut ke [07-SEARCH_ENGINE.md](07-SEARCH_ENGINE.md) - Elasticsearch Integration
