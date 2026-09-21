from django.urls import path, include
from .routers import router
from .swagger import schema_view
from .views import CategoryList

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('custom/', CategoryList.as_view()),
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
