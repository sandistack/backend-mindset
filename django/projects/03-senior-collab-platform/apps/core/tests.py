"""
Tests for core app functionality.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from apps.core.models import BaseModel, SoftDeleteModel
from django.db import models


class TestModel(BaseModel):
    """Test model for testing BaseModel."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class TestSoftDeleteModel(SoftDeleteModel):
    """Test model for testing SoftDeleteModel."""
    title = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


@pytest.mark.django_db
class TestBaseModel:
    """Tests for BaseModel functionality."""
    
    def test_uuid_primary_key(self):
        """Test that BaseModel uses UUID as primary key."""
        obj = TestModel.objects.create(name="Test")
        assert isinstance(obj.id, type(obj.id))  # UUID type
        assert len(str(obj.id)) == 36  # UUID format
    
    def test_timestamps(self):
        """Test that timestamps are created automatically."""
        obj = TestModel.objects.create(name="Test")
        assert obj.created_at is not None
        assert obj.updated_at is not None
        assert obj.created_at <= obj.updated_at


@pytest.mark.django_db
class TestSoftDeleteModel:
    """Tests for SoftDeleteModel functionality."""
    
    def test_soft_delete(self):
        """Test soft delete functionality."""
        obj = TestSoftDeleteModel.objects.create(title="Test")
        obj.delete()
        
        # Object should be marked as deleted
        assert obj.is_deleted
        assert obj.deleted_at is not None
        
        # Should not appear in default queryset
        assert TestSoftDeleteModel.objects.count() == 0
        
        # Should appear in all_objects queryset
        assert TestSoftDeleteModel.all_objects.count() == 1
    
    def test_hard_delete(self):
        """Test hard delete removes object from database."""
        obj = TestSoftDeleteModel.objects.create(title="Test")
        obj.hard_delete()
        
        # Should not exist at all
        assert TestSoftDeleteModel.all_objects.count() == 0
    
    def test_restore(self):
        """Test restore functionality."""
        obj = TestSoftDeleteModel.objects.create(title="Test")
        obj.delete()  # Soft delete
        obj.restore()
        
        # Should be restored
        assert not obj.is_deleted
        assert obj.deleted_at is None
        assert TestSoftDeleteModel.objects.count() == 1
