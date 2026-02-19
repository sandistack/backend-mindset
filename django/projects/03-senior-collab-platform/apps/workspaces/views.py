"""
Views for workspace management.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def placeholder(request):
    """Placeholder view - will be implemented in next steps."""
    return Response({'message': 'Workspaces API'})
