from django.core.management.base import BaseCommand
from .python_models import Family
import io


class Command(BaseCommand):

    def handle(self, *args, **options):
        from rest_framework import serializers

        class FamilySerializer(serializers.Serializer):
            name = serializers.CharField(max_length=128)
            max_age = serializers.IntegerField()

        # 1. Сериализация в python объект
        family = Family('Медведь', 50)
        serializer = FamilySerializer(family)
        # data переобразует в словарь
        print(serializer.data)  # {'name': 'Медведь', 'max_age': 50}
        print(type(serializer.data))  # <class 'rest_framework.utils.serializer_helpers.ReturnDict'>
        #JSONRenderer это для примера есть другие
        # https://www.django-rest-framework.org/api-guide/renderers/#varying-behavior-by-media-type
        from rest_framework.renderers import JSONRenderer
        renderer = JSONRenderer()
        # renderer преобразыет словать в json с байтими
        json_bytes = renderer.render(serializer.data)
        print(json_bytes)  # b'{"name":"\xd0\x9c\xd0\xb5\xd0\xb4\xd0\xb2\xd0\xb5\xd0\xb4\xd1\x8c","max_age":50}'
        print(type(json_bytes))  # <class 'bytes'>

        # обратный эфект JSONParser приводит быйты в словарь
        from rest_framework.parsers import JSONParser
        # Читаем байты и записываем в stream
        stream = io.BytesIO(json_bytes)

        data = JSONParser().parse(stream)
        print(data)  # {'name': 'Медведь', 'max_age': 50}
        print(type(data))  # <class 'dict'>

        # пердаем сериалаизер (FamilySerializer) для подстановке данных к модели
        serializer = FamilySerializer(data=data)
        print(serializer.is_valid())  # True
        print(serializer.validated_data)  # OrderedDict([('name', 'Медведь'), ('max_age', 50)])
        print(type(serializer.validated_data))  # <class 'collections.OrderedDict'>

        {"my_field": 123} # {"myField": 123}