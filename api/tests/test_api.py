from rest_framework.test import APITestCase, APIClient
from mixer.backend.django import mixer

from mainapp.models import Category
from userapp.models import MyUser


# APITestCase 95% теста через него, проверка запрос ответ
class CategoryViewSetApiTest(APITestCase):
    # Создаем юзера для тестов с индификацией и авторизацией
    # if setting 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    def setUp(self):
        # Юзер автореированный
        user = MyUser.objects.create_user("user", "user@ya.ru", "user")  # noqa: S106
        self.client.force_authenticate(user=user)  # noqa: S106

        # втрой юзер для теста
        self.guest_client = APIClient()

        # админ # noqa: S106
        self.admin_client = APIClient()
        user = MyUser.objects.create_superuser("admin", "admin@ya.ru", "admin")  # noqa: S106"
        self.admin_client.force_authenticate(user=user)  # noqa: S106)

    def test_list_status_code(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)

    def test_list_status_code_guest(self):
        response = self.guest_client.get('/api/categories/')
        self.assertEqual(response.status_code, 401)

    # база не подключена в момент запроса, по этому пустой ответ
    def test_list_empty_response(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.json(), {'count': 0, 'next': None, 'previous': None, 'results': []})

    # проверка на непустой ответ. создать данные записать в базу и проверить что ответ не пустой
    def test_list_not_empty_response(self):
        mixer.blend(Category, name='Медведь')
        mixer.blend(Category, name='Тигр')
        # Убедимся, что обе категории созданы
        self.assertEqual(Category.objects.count(), 2)
        response = self.client.get('/api/categories/')
        data = response.json()
        # PAGE_SIZE=1, поэтому на первой странице 1 результат
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 1)
        # Проверяем, что результат содержит созданную категорию
        self.assertIn(data['results'][0]['name'], ['Медведь', 'Тигр'])

    # проверка что создание категории работает
    def test_create_category(self):
        data = {
            'name': 'Новое животное',
        }
        self.assertFalse(Category.objects.all().exists())
        response = self.client.post(
            '/api/categories/',
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(1, Category.objects.all().count())

    # + тесты на обновление и удаление категории





