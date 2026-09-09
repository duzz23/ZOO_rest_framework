from rest_framework import serializers
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):

        class FamilySerializer(serializers.Serializer):
            name = serializers.CharField(max_length=128)
            max_age = serializers.IntegerField()
            # max_age = serializers.IntegerField()
            """Еще пример КАСТОМНОЙ ВАЛИДАЦИИ"""
            # что бы метод работал имя долно начинаться с validate_{любое имя}
            def validate_max_age(self, value):
                print('validate max age')
                if value < 0:
                    raise serializers.ValidationError('Максимальный возраст не может быть отрицательным')
                return value
            """Валидация все полей вместе"""
            # что бы метод работал имя долно начинаться с validate_{любое имя}
            def validate(self, attrs):
                print('validate')
                if attrs['name'] == 'Медведь' and attrs['max_age'] < 3:
                    raise serializers.ValidationError('Медведи живут больше')
                return attrs

        data = {'name': 'Тигр', 'max_age': 30}
        serializer = FamilySerializer(data=data)
        print(serializer.is_valid())

        data = {'name': 'Черепаха', 'max_age': -10}
        serializer = FamilySerializer(data=data)
        print(serializer.is_valid())

        print(serializer.errors)

        data = {'name': 'Медведь', 'max_age': 2}
        serializer = FamilySerializer(data=data)
        print(serializer.is_valid())

        print(serializer.errors)

# validate max age
# validate
# True
# validate max age
# False
# {'max_age': [ErrorDetail(string='Максимальный возраст не может быть отрицательным', code='invalid')]}
# validate max age
# validate
# False
# {'non_field_errors': [ErrorDetail(string='Медведи живут больше', code='invalid')]}