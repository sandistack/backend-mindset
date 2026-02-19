"""
Base serializers with common functionality.
"""

from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common fields and methods"""
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that allows dynamic field selection via query params.
    
    Usage:
        ?fields=id,name,email
        ?omit=created_at,updated_at
    """
    
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        omit = kwargs.pop('omit', None)
        
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        if omit is not None:
            # Drop fields specified in the `omit` argument
            for field_name in omit:
                self.fields.pop(field_name, None)
