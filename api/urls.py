from django.urls import path, include
from .routers import router as category_router
from .views import CategoryList

app_name = 'api'

urlpatterns = [
    path('', include(category_router.urls)),
    path('custom/', CategoryList.as_view()),
]
