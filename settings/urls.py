from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainapp.urls')),
    path('users/', include('userapp.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
    # api-auth для индификации по токену
    path('api-auth/', include('rest_framework.urls')),
    # api-token-auth для выпуска токена
    path('api-token-auth/', views.obtain_auth_token),
    # router
    path('api/', include('api.urls')),
]
