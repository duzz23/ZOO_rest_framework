from django_filters import rest_framework as filters
from mainapp.models import Animal

"Этот фильтр поможет искать совподения по имени."
class ProductFilter(filters.FilterSet):
    # (lookup expression). Оно транслируется в SQL-запрос и определяет, как именно база данных должна сравнивать значение из URL с данными в таблице.
    # exact: Точное совпадение (WHERE name = '...'). Регистр учитывается.
    # iexact: Точное совпадение без учета регистра.
    # startswith / istartswith: Строка начинается с...
    # endswith / iendswith: Строка заканчивается на...
    # in: Значение находится в списке (например, ?id__in=1,5,9).
    # isnull: Проверка на пустоту значения
    name = filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Animal
        fields = ['name']

