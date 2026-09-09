from rest_framework import serializers
from mainapp.models import Category, Animal


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AnimalSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    # HyperlinkedIdentityField что бы сдалать ссылку на переход на объект
    # пример: "category": "http://127.0.0.1:8000/api/categories/9/",
    # category = serializers.HyperlinkedIdentityField(view_name="api:category-detail", read_only=True)
    food = serializers.StringRelatedField(many=True)

    class Meta:
        model = Animal
        fields = '__all__'

# AnimalSerializer вот так это выглядит в jsone()
#
# [
#     {
#         "id": 9,
#         "category": {
#             "id": 11,
#             "create": "2026-09-08T20:36:21.093266Z",
#             "create_duplicated": "2026-09-08T20:36:21.093280Z",
#             "update": "2026-09-08T20:36:21.093286Z",
#             "name": "Медведь"
#         },
#         "food": [
#             "Мясо",
#             "Мед"
#         ],
#         "create": "2026-09-08T20:36:21.094823Z",
#         "create_duplicated": "2026-09-08T20:36:21.094829Z",
#         "update": "2026-09-08T20:36:21.097434Z",
#         "name": "Борис",
#         "a": 1,
#         "b": 1,
#         "d": 2
#     }
# ]