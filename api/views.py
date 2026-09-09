from rest_framework import viewsets, views, response
from mainapp.models import Category, Animal
from .serializers import CategorySerializer, AnimalSerializer

# из коробки viewsets
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

# Кастомный viewsets
class CategoryList(views.APIView):

    def get(self, request, format=None):
        quetyset = Category.objects.all()
        serializer = CategorySerializer(quetyset, many=True)
        response_json = serializer.data
        # return response.Response({})
        return response.Response(response_json)


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer