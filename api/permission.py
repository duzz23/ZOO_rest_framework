from rest_framework import permissions

# Свой класс разрешения доступа к API
class IsFoodMaster(permissions.BasePermission):
   def has_permission(self, request, view):
       return request.user.is_food_master