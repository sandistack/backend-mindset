from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def placeholder(request):
    return Response({'message': 'Documents API'})

app_name = 'documents'
urlpatterns = [path('', placeholder)]
