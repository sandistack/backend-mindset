"""
Base models for all apps in the platform.
Provides common functionality like UUID primary keys, timestamps, and soft delete.
"""

from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
    All models should inherit from this.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when record was last updated"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return str(self.id)


class SoftDeleteQuerySet(models.QuerySet):
    """Custom QuerySet for soft delete functionality"""
    
    def delete(self):
        """Soft delete all objects in the queryset"""
        from django.utils import timezone
        return self.update(is_deleted=True, deleted_at=timezone.now())
    
    def hard_delete(self):
        """Permanently delete all objects in the queryset"""
        return super().delete()
    
    def alive(self):
        """Return only non-deleted objects"""
        return self.filter(is_deleted=False)
    
    def dead(self):
        """Return only deleted objects"""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default"""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def with_deleted(self):
        """Include soft-deleted objects"""
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(BaseModel):
    """
    Abstract base model with soft delete functionality.
    Objects are marked as deleted instead of being removed from database.
    """
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates if record is soft-deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when record was deleted"
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the object"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self):
        """Permanently delete the object"""
        super().delete()
    
    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class TimestampedModel(models.Model):
    """
    Abstract model providing timestamp fields.
    Use this if you don't need UUID primary keys.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
