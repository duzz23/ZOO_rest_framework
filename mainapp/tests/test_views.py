from django.test import TestCase, Client


class TestIndexViews(TestCase):
    # провкерка статуса кода, проверку надо делать на все страницы
    def test_status_code(self):
        # client встроен в TestCase (передаем адрес без домена)
        response = self.client.get('/')
        # какой именно статус ожидаеться
        self.assertEqual(response.status_code, 200)

    # тест что на страницу переданы данные (в index_view() есть передача контеста)
    def test_context(self):
        response = self.client.get('/')
        context = response.context
        self.assertIn('title', context)
        # assertEqual сравнение объектов и их значений на равенство
        self.assertEqual('Главная страница', context['title'])  # 'Главная страница

    # тестирование елиментов или парсинг страницы (content)
    def test_content(self):
        response = self.client.get('/')
        content = response.content
        # дальше добавляем любую логику
        # Проверка на наличие текста в заголовке Welcome to Zo
        self.assertIn(b'Welcome to Zo', content)  # b'Welcome to Zo' (bytes)
        # тоже самое только байти в строке переводим
        self.assertIn('Welcome to Zoo', content.decode("utf-8"))
        # метод assertContains() проверяет, что в ответе содержится указанный фрагмент.
        # count сколько раз встречается фрагмент
        # status_code код ответа
        self.assertContains(response, 'Welcome to Zoo', count=1, status_code=200)

