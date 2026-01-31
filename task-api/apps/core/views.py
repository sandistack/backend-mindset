# apps/core/views.py
"""
Core API endpoints

Admin only: Audit log access restricted
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditLogListView(APIView):
    """
    GET /api/admin/audit-logs/
    
    List audit logs (Admin only)
    
    Secure: Only admins can access
    """
    
    permission_classes = [IsAdminUser]
    pagination_class = AuditLogPagination
    
    def get(self, request):
        """
        List audit logs with filters
        
        Query params:
            - user: Filter by username
            - action: CREATE, UPDATE, DELETE, ERROR
            - feature: task, user, etc.
            - status: SUCCESS, FAILED
        
        Admin tool: Monitor system activity
        """
        
        queryset = AuditLog.objects.all()
        
        # Filters
        user_filter = request.query_params.get('user')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        
        action_filter = request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        feature_filter = request.query_params.get('feature')
        if feature_filter:
            queryset = queryset.filter(feature__icontains=feature_filter)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Paginate
        paginator = self.pagination_class()
        paginated_logs = paginator.paginate_queryset(queryset, request)
        
        # Serialize
        serializer = AuditLogSerializer(paginated_logs, many=True)
        
        return paginator.get_paginated_response({
            'success': True,
            'message': 'Audit logs retrieved successfully',
            'data': serializer.data
        })
