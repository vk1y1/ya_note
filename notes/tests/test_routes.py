"""Тестирование маршрутов проекта YaNotes."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Фикстуры для теста маршрутов."""
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не Автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )
        cls.users_statuses = (
            (cls.author, HTTPStatus.OK),
            (cls.not_author, HTTPStatus.NOT_FOUND),
        )
        cls.login_url = reverse('users:login')
        cls.urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None)
        )
        cls.urls_list_add_success = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None)
        )
        cls.urls_slug = (
            ('notes:detail', (cls.note.slug,)),
            ('notes:edit', (cls.note.slug,)),
            ('notes:delete', (cls.note.slug,))
        )

    def get_response_status_code(
            self,
            urls,
            user=None,
            is_status_code=True,
            is_redirect=False,
            status=HTTPStatus.OK
    ):
        """
        Проверяет доступность и переадресацию страниц.

        Распаковывает кортеж с данными для адреса для каждого элемента из urls,
        генерирует URL-адрес, получает ответ на запрос страницы клиентом и в
        зависимости от флагов проверяет доступность страниц для разных
        пользователей или переадресацию на страницу авторизации.

        Параметры:
            urls: имя URL-паттерна с позиционными аргументами(если есть)
            user: объект пользователя
            is_status_code: флаг проверки доступности сраницы
            is_redirect: флаг проверки переадресации на страницу авторизации
            status: статус код страницы
        """
        for name, args in urls:
            with self.subTest(user=user, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                if is_status_code:
                    self.assertEqual(response.status_code, status)
                if is_redirect:
                    redirect_url = f'{self.login_url}?next={url}'
                    self.assertRedirects(response, redirect_url)

    def test_pages_availability(self):
        """Проверяет доступность страниц анонимному пользователю."""
        self.get_response_status_code(self.urls)

    def test_availability_for_list_add_success(self):
        """Проверяет доступность страниц notes/, done/ и add/."""
        self.client.force_login(self.author)
        self.get_response_status_code(self.urls_list_add_success)

    def test_availability_for_note_detail_edit_delete(self):
        """Проверяет доступность страниц заметки, удаления и редактирования."""
        for user, status in self.users_statuses:
            self.client.force_login(user)
            self.get_response_status_code(
                self.urls_slug,
                user=user,
                status=status
            )

    def test_redirect_for_anonymous_client(self):
        """Проверяет переадресацию анонима на страницу авторизации."""
        self.get_response_status_code(
            self.urls_list_add_success + self.urls_slug,
            is_status_code=False,
            is_redirect=True,
            status=None
        )
