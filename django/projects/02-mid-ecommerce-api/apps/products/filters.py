"""
Filters for Product catalog.
"""

import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """Filter products by price, category, stock, featured."""
    
    # Price range filter
    min_price = django_filters.NumberFilter(
        field_name='base_price', 
        lookup_expr='gte',
        label='Minimum Price'
    )
    max_price = django_filters.NumberFilter(
        field_name='base_price', 
        lookup_expr='lte',
        label='Maximum Price'
    )
    
    # Category filter (includes subcategories)
    category = django_filters.NumberFilter(
        method='filter_category',
        label='Category'
    )
    
    # In stock filter
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='In Stock Only'
    )
    
    # Featured filter
    is_featured = django_filters.BooleanFilter(
        field_name='is_featured',
        label='Featured Products'
    )
    
    class Meta:
        model = Product
        fields = ['category', 'is_featured', 'in_stock', 'min_price', 'max_price']
    
    def filter_category(self, queryset, name, value):
        """
        Filter by category and all its subcategories.
        Example: If filter by "Electronics", also show products in "Electronics > Phones".
        """
        try:
            category = Category.objects.get(pk=value)
            # Get all descendants (child categories)
            descendants = category.get_descendants()
            # Include the category itself + all children
            category_ids = [category.id] + [c.id for c in descendants]
            return queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()
    
    def filter_in_stock(self, queryset, name, value):
        """
        Filter products that have stock.
        Checks if any variant has stock > 0.
        """
        if value:
            return queryset.filter(variants__stock__gt=0).distinct()
        return queryset
