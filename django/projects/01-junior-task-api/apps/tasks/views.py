from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Category, Task
from .serializers import (
    CategorySerializer,
    TaskSerializer,
    TaskCreateUpdateSerializer,
    TaskDetailSerializer
)
from apps.core.permissions import IsOwner


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations
    
    list: Get all user's categories
    create: Create new category
    retrieve: Get category detail
    update: Update category
    partial_update: Partial update category
    destroy: Delete category
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        """
        Filter categories by current user
        """
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Set user automatically when creating category
        """
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Categories retrieved successfully',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Category created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Category retrieved successfully',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'message': 'Category updated successfully',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Category deleted successfully'
        }, status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations with soft delete
    
    list: Get all user's tasks (excluding deleted)
    create: Create new task
    retrieve: Get task detail
    update: Update task
    partial_update: Partial update task
    destroy: Soft delete task
    complete: Mark task as complete
    restore: Restore soft-deleted task
    """
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        """
        Filter tasks by current user (excluding soft-deleted by default)
        """
        return Task.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions
        """
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """
        Set user automatically when creating task
        """
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return with full task serializer
        task = Task.objects.get(pk=serializer.instance.pk)
        response_serializer = TaskSerializer(task)
        
        return Response({
            'success': True,
            'message': 'Task created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Task retrieved successfully',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # If status changed to 'done', mark as complete
        if serializer.validated_data.get('status') == 'done' and instance.status != 'done':
            instance.mark_complete()
        
        # Return with full task serializer
        response_serializer = TaskSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Task updated successfully',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the task instead of hard delete
        """
        instance = self.get_object()
        instance.soft_delete()
        return Response({
            'success': True,
            'message': 'Task deleted successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Custom action to mark task as complete
        
        POST /api/tasks/{id}/complete/
        """
        task = self.get_object()
        task.mark_complete()
        serializer = TaskSerializer(task)
        
        return Response({
            'success': True,
            'message': 'Task marked as complete',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Custom action to restore soft-deleted task
        
        POST /api/tasks/{id}/restore/
        """
        # Need to get from all_objects to include deleted tasks
        task = get_object_or_404(
            Task.all_objects.filter(user=request.user),
            pk=pk
        )
        
        if not task.is_deleted:
            return Response({
                'success': False,
                'message': 'Task is not deleted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.restore()
        serializer = TaskSerializer(task)
        
        return Response({
            'success': True,
            'message': 'Task restored successfully',
            'data': serializer.data
        })
