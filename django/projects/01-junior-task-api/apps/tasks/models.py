from django.db import models
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    """
    Category model for organizing tasks
    """
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        unique_together = ['name', 'user']  # User tidak boleh punya category dengan nama sama
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"


class TaskManager(models.Manager):
    """
    Custom manager untuk Task yang exclude soft-deleted tasks by default
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Task(models.Model):
    """
    Task model with soft delete support
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Managers
    objects = TaskManager()  # Default: exclude deleted tasks
    all_objects = models.Manager()  # Include all tasks (even deleted)
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.user.email})"
    
    def mark_complete(self):
        """
        Mark task as complete
        """
        self.status = 'done'
        self.completed_at = timezone.now()
        self.save()
    
    def soft_delete(self):
        """
        Soft delete the task (set is_deleted=True)
        """
        self.is_deleted = True
        self.save()
    
    def restore(self):
        """
        Restore soft-deleted task
        """
        self.is_deleted = False
        self.save()
