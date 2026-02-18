import django_filters
from django.utils import timezone
from .models import Task, Category


class TaskFilter(django_filters.FilterSet):
    """
    FilterSet for Task model with advanced filtering options
    """
    # Exact match filters
    status = django_filters.CharFilter(field_name='status')
    priority = django_filters.CharFilter(field_name='priority')
    category = django_filters.NumberFilter(field_name='category__id')
    
    # Date range filters for due_date
    due_date_from = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte',
        label='Due date from'
    )
    due_date_to = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte',
        label='Due date to'
    )
    
    # Date range filters for created_at
    created_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created from'
    )
    created_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created to'
    )
    
    # Boolean custom filters
    is_completed = django_filters.BooleanFilter(
        method='filter_is_completed',
        label='Is completed'
    )
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue',
        label='Is overdue'
    )
    has_category = django_filters.BooleanFilter(
        method='filter_has_category',
        label='Has category'
    )
    
    class Meta:
        model = Task
        fields = ['status', 'priority', 'category']
    
    def filter_is_completed(self, queryset, name, value):
        """
        Filter tasks by completion status
        """
        if value:
            return queryset.filter(status='done')
        return queryset.exclude(status='done')
    
    def filter_is_overdue(self, queryset, name, value):
        """
        Filter overdue tasks (past due_date and not completed)
        """
        now = timezone.now()
        if value:
            return queryset.filter(
                due_date__lt=now,
                status__in=['pending', 'in_progress']
            )
        return queryset
    
    def filter_has_category(self, queryset, name, value):
        """
        Filter tasks with or without category
        """
        if value:
            return queryset.filter(category__isnull=False)
        return queryset.filter(category__isnull=True)


class CategoryFilter(django_filters.FilterSet):
    """
    FilterSet for Category model
    """
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Name contains'
    )
    color = django_filters.CharFilter(
        lookup_expr='exact',
        label='Exact color'
    )
    
    class Meta:
        model = Category
        fields = ['name', 'color']
