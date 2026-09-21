from rest_framework import routers
from .views import CategoryViewSet, AnimalViewSetMixins

# https://www.django-rest-framework.org/api-guide/routers/
# Задача роутера генерировать адреса используется с viewsets
# используется с DefaultRouter и SimpleRouter
router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet)
# router.register(r'animas', AnimalViewSet)
router.register(r'animas', AnimalViewSetMixins)
