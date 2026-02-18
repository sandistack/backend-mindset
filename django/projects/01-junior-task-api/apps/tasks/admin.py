from django.contrib import admin
from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category
    """
    list_display = ['name', 'color', 'user', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'user__email']
    ordering = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin configuration for Task
    """
    list_display = ['title', 'user', 'category', 'priority', 'status', 'due_date', 'is_deleted', 'created_at']
    list_filter = ['status', 'priority', 'is_deleted', 'created_at', 'category']
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at', 'created_at', 'updated_at')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted',)
        }),
    )
    
    def get_queryset(self, request):
        # Show all tasks including deleted in admin
        return Task.all_objects.all()
