from django.urls import path, include
from .routers import router
from .views import CategoryList

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('custom/', CategoryList.as_view()),
]
