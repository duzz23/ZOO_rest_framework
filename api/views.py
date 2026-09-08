from rest_framework import viewsets, views, response
from mainapp.models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

#
class CategoryList(views.APIView):

    def get(self, request, format=None):
        quetyset = Category.objects.all()
        serializer = CategorySerializer(quetyset, many=True)
        response_json = serializer.data
        # return response.Response({})
        return response.Response(response_json)
