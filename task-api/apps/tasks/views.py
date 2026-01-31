# apps/tasks/views.py
"""
Task API endpoints

RESTful: Standard CRUD operations
Thin views: Business logic in services
Secure: Permission checks
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Task
from .serializers import TaskSerializer, TaskCreateUpdateSerializer
from .services import TaskService

from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger('apps')


class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class
    
    Scalable: Handle large datasets
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskListCreateView(APIView):
    """
    GET  /api/tasks/        - List all tasks
    POST /api/tasks/        - Create new task
    
    RESTful: Single endpoint for list & create
    """
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        """
        List user's tasks with filters
        
        Query params:
            - status: TODO, IN_PROGRESS, DONE
            - priority: LOW, MEDIUM, HIGH
            - search: Search in title/description
            - page: Page number
            - page_size: Items per page
        
        Response:
            {
                "success": true,
                "message": "Tasks retrieved successfully",
                "data": {
                    "count": 50,
                    "next": "http://...",
                    "previous": null,
                    "results": [...]
                }
            }
        
        Scalable: Pagination for large datasets
        Maintainable: Filtering logic in service
        """
        
        # Get filters from query params
        filters = {
            'status': request.query_params.get('status'),
            'priority': request.query_params.get('priority'),
            'search': request.query_params.get('search'),
        }
        
        # Call service
        tasks = TaskService.get_user_tasks(
            user=request.user,
            filters=filters
        )
        
        # Paginate
        paginator = self.pagination_class()
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        
        # Serialize
        serializer = TaskSerializer(paginated_tasks, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'data': serializer.data
        })
    
    def post(self, request):
        """
        Create new task
        
        Request body:
            {
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "status": "TODO",
                "priority": "HIGH",
                "due_date": "2026-02-01T10:00:00Z"
            }
        
        Response:
            {
                "success": true,
                "message": "Task created successfully",
                "data": {...}
            }
        
        Secure: User from request.user, not from input
        """
        
        # Validate input
        serializer = TaskCreateUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Call service
            task = TaskService.create_task(
                user=request.user,
                validated_data=serializer.validated_data,
                request=request
            )
            
            # Return created task
            return Response({
                'success': True,
                'message': 'Task created successfully',
                'data': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Task creation error: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'message': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskDetailView(APIView):
    """
    GET    /api/tasks/{id}/  - Get task detail
    PUT    /api/tasks/{id}/  - Update task
    PATCH  /api/tasks/{id}/  - Partial update task
    DELETE /api/tasks/{id}/  - Delete task
    
    RESTful: Single endpoint for detail operations
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        """
        Helper to get task and check ownership
        
        DRY: Reused across methods
        Secure: Check ownership
        """
        task = get_object_or_404(Task, pk=pk)
        
        # Check permission
        if not TaskService.can_user_edit_task(user, task):
            return None
        
        return task
    
    def get(self, request, pk):
        """
        Get task detail
        
        Response:
            {
                "success": true,
                "message": "Task retrieved successfully",
                "data": {...}
            }
        """
        
        task = self.get_object(pk, request.user)
        
        if not task:
            return Response({
                'success': False,
                'message': 'Task not found or access denied',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Task retrieved successfully',
            'data': TaskSerializer(task).data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Full update task
        
        Request body:
            {
                "title": "Updated title",
                "description": "Updated description",
                "status": "IN_PROGRESS",
                "priority": "MEDIUM",
                "due_date": "2026-02-01T10:00:00Z"
            }
        """
        return self._update_task(request, pk, partial=False)
    
    def patch(self, request, pk):
        """
        Partial update task
        
        Request body:
            {
                "status": "DONE"
            }
        
        Flexible: Only update provided fields
        """
        return self._update_task(request, pk, partial=True)
    
    def _update_task(self, request, pk, partial):
        """
        Shared update logic
        
        DRY: Avoid code duplication
        """
        
        task = self.get_object(pk, request.user)
        
        if not task:
            return Response({
                'success': False,
                'message': 'Task not found or access denied',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate input
        serializer = TaskCreateUpdateSerializer(
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Call service
            updated_task = TaskService.update_task(
                task=task,
                validated_data=serializer.validated_data,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Task updated successfully',
                'data': TaskSerializer(updated_task).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Task update error: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'message': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """
        Delete task
        
        Response:
            {
                "success": true,
                "message": "Task deleted successfully",
                "data": null
            }
        """
        
        task = self.get_object(pk, request.user)
        
        if not task:
            return Response({
                'success': False,
                'message': 'Task not found or access denied',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check delete permission
        if not TaskService.can_user_delete_task(request.user, task):
            return Response({
                'success': False,
                'message': 'You do not have permission to delete this task',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Call service
            TaskService.delete_task(task=task, request=request)
            
            return Response({
                'success': True,
                'message': 'Task deleted successfully',
                'data': None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Task deletion error: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'message': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)