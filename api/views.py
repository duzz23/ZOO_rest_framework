from django.db.models.functions.math import Log
from rest_framework import viewsets, views, response, generics, mixins
from mainapp.models import Category, Animal
from .filters import ProductFilter
from .paginators import TimezonePagination
from .serializers import CategorySerializer, AnimalSerializer, AnimalCreateSerializer
from rest_framework.decorators import action


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

"""Тестируем разные VIEWS для Классф"""

# адреc прописываетья в routers
# class AnimalViewSet(viewsets.ModelViewSet):
#     queryset = Animal.objects.all()
#     serializer_class = AnimalSerializer

# Если хотим получить только списов всех животных
# адреc прописываетья в url
# + еще варианты Клсса: https://www.django-rest-framework.org/api-guide/generic-views/#listapiview
# class AnimalListView(generics.ListAPIView):
#     queryset = Animal.objects.all()
#     serializer_class = AnimalSerializer

# Самый оптимальный VIEWSET - Custom ViewSet base classes
# https://www.django-rest-framework.org/api-guide/viewsets/#custom-viewset-base-classes

# mixins.ListModelMixin - представление которое мы хотим получить,
# mixins.CreateModelMixin, - представление которое мы хотим получить,
# mixins.RetrieveModelMixin - представление которое мы хотим получить,
# viewsets.GenericViewSet - обязательный класс всегда
class AnimalViewSetMixins(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = AnimalSerializer
    queryset = Animal.objects.all()
    # Простой фильтр
    # filterset_fields = ['name']
    # делаем свой фильтр. На совподения.
    filterset_class = ProductFilter
    #Свой пагинатор
    pagination_class = TimezonePagination

    """Важно Фильтрация
    Для вашего проекта оптимальной стратегией будет комбинированный подход: 
    используйте DjangoFilterBackend для основной массы фильтров, 
    добавьте OrderingFilter для удобства пользователя, 
    а специфическую логику (привязку к профилю пользователя) вынесите в пере
    определение get_queryset().
    get_queryset добавим метод получения из БД что бы миновать болшой щапрос N+1
    """
    def get_queryset(self):
        return Animal.objects.all().prefetch_related('food')

    """Важно"""
    # https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing
    # @action для реализации кастомных методов, DRF автоматически генерирует для него новый URL-шаблон и связывает его с этим методом.
    @action(detail=True, methods=['get'])
    def log_animal(self, request, pk=None):
        animal = self.get_object()
        print("Log animal")
        print(animal)
        return response.Response({"status": "done.."})
    """Важно"""
    # Метод позволяет выбрать сериализатор в зависимости от действия AnimalCreateSerializer или AnimalSerializer
    def get_serializer_class(self):
        if self.action == 'create':
            return AnimalCreateSerializer
        return AnimalSerializer

    # Общая фильтрация
    # https://www.django-rest-framework.org/api-guide/filtering/#filtering-against-query-parameters
