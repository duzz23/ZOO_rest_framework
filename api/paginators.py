# Кастомная Пагинация
from datetime import datetime

from rest_framework import pagination, response

class TimezonePagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return response.Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data,
            'curent_time': datetime.now()
        })

# Так бысрее работает пагинация так как не надо загружать весь список старниц + скрытность количество страниуц
class CustomCursorPagination(pagination.CursorPagination):
    ordering = '-create'
