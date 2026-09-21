import requests


url = 'http://127.0.0.1:8000/api/categories/'

response = requests.get(url)
assert 401 == response.status_code, response.status_code

login = "user"
password = "user"
response = requests.get(url, auth=(login, password))
assert 200 == response.status_code, response.status_code

#Получаем токен, слабый для пет проектов
data = {
    "username": "admin",
    "password": "admin",
}
url = 'http://127.0.0.1:8000/api-token-auth/'
response = requests.post(url=url, data=data)
token = response.json()['token']

headers = {
        "Authorization": f"Token {token}"
    }

url = 'http://127.0.0.1:8000/api/categories/'

response = requests.get(url, headers=headers)
assert 200 == response.status_code, response.status_code

# Для рабочих проектов нужен JWT_TOKET https://jpadilla.github.io/django-rest-framework-jwt/

# Часто используется токены для аутификации JSON Web Token Authentication(для средних проектов) и Djoser(для больших проектов)
# https://www.django-rest-framework.org/api-guide/authentication/#installation-configuration_1

url = 'http://127.0.0.1:8000/api/animas/'


# login = "user"
# password = "user"
# response = requests.get(url, auth=(login, password))
# assert 404 == response.status_code, response.status_code

login = "food_master"
password = "food_master"
response = requests.get(url, auth=(login, password))
assert 200 == response.status_code, response.status_code