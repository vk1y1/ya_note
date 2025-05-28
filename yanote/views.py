"""Создание кастомного представления для обхода ошибки 405."""
from django.contrib.auth.views import LogoutView


class CustomLogoutView(LogoutView):
    """Представление страницы logout через post запрос."""

    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        """Переопределяет метод get."""
        return super().post(request, *args, **kwargs)
