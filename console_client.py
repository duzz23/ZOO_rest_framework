import requests


url = 'http://127.0.0.1:8000/api/categories/'


# HEAD
# response = requests.head(url)
# print(response.status_code)
# print(response.headers)


# GET
# response = requests.get(url)
# print(response.status_code)
# response_json = response.json()
# print(response.json())
# print(type(response_json))


# POST
# data = {
#     'name': 'New Animal',
# }
#
# response = requests.post(url, json=data)
# print(response.status_code)  # 201
# print(response.json())

# OPTIONS

# response = requests.options(url)
# print(response.status_code)  # 200
# print(response.json())

url = 'http://127.0.0.1:8000/api/categories/6/'

# # HEAD
# response = requests.head(url)
# print(response.status_code)
# print(response.headers)
#
#
# # GET
# response = requests.get(url)
# print(response.status_code)
# response_json = response.json()
# print(response.json())
# print(type(response_json))
#
#
# # OPTIONS
#
# response = requests.options(url)
# print(response.status_code)  # 200
# print(response.json())

# PUT

# data = {
#     'name': 'New Animal Put',
# }
#
# response = requests.put(url, json=data)
# print(response.status_code)  # 200
# print(response.json())

# PATCH

# data = {
#     'name': 'New Animal Patch',
# }
#
# response = requests.put(url, json=data)
# print(response.status_code)  # 200
# print(response.json())

# DELETE

response = requests.delete(url)
print(response.status_code)  # 204
# print(response.json())
