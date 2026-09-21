from rest_framework import serializers
from mainapp.models import Category, Animal


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# Это сериализатор будут для показа
class AnimalSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    # HyperlinkedIdentityField что бы сдалать ссылку на переход на объект
    # пример: "category": "http://127.0.0.1:8000/api/categories/9/",
    # category = serializers.HyperlinkedIdentityField(view_name="api:category-detail", read_only=True)
    food = serializers.StringRelatedField(many=True)

    class Meta:
        model = Animal
        fields = '__all__'

# Это сериализатор будут для сохранения
class AnimalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = '__all__'
