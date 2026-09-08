from django.core.management.base import BaseCommand
from mainapp.models import Category, Food, Animal, WildAnimal, HomeAnimal, LoggingAnimal, AnimalCard
from django.db import transaction


class Command(BaseCommand):
    help = "Заполняет базу тестовыми животными, категориями и едой"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Создание тестовых данных..."))

        # Очистим старые записи
        AnimalCard.objects.all().delete()
        Animal.objects.all().delete()
        Food.objects.all().delete()
        Category.objects.all().delete()

        # Категории
        bear_cat = Category.objects.create(name="Медведь")
        tiger_cat = Category.objects.create(name="Тигр")
        monkey_cat = Category.objects.create(name="Обезьяна")

        # Еда
        meat = Food.objects.create(name="мясо")
        banana = Food.objects.create(name="банан")

        # Животные
        tiger_boris = Animal.objects.create(name="Тигр Борис", category=tiger_cat)
        tiger_boris.food.add(meat)

        bear_misha = WildAnimal.objects.create(name="Медведь Миша", category=bear_cat, age=5)
        bear_misha.food.add(meat)

        monkey_kiki = HomeAnimal.objects.create(name="Обезьяна Кики", category=monkey_cat, last_owner_name="Анна")
        monkey_kiki.food.add(banana, meat)

        # LoggingAnimal
        log_animal = LoggingAnimal.objects.create(name="Тигр Лог", category=tiger_cat)
        log_animal.food.add(meat)

        # Animal Cards
        AnimalCard.objects.create(animal=tiger_boris, text="Карточка Бориса")
        AnimalCard.objects.create(animal=bear_misha, text="Карточка Миши")
        AnimalCard.objects.create(animal=monkey_kiki, text="Карточка Кики")
        AnimalCard.objects.create(animal=log_animal, text="Карточка Лога")

        self.stdout.write(self.style.SUCCESS("Готово! Данные успешно добавлены."))
