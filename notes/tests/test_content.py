"""Тестирование контента проекта YaNote."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestListDetailPage(TestCase):
    """Тестирование страниц списка и отдельной заметки."""

    @classmethod
    def setUpTestData(cls):
        """Фикстуры для теста контента."""
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )
        cls.list_url = reverse('notes:list')
        cls.edit_url = reverse('notes:edit',
                               args=(cls.note.slug,))
        cls.add_url = reverse('notes:add')

    def test_note_in_list_author(self):
        """Поверяет передачу отдельной заметки на страницу со списком."""
        self.client.force_login(self.author)
        response = self.client.get(self.list_url)
        object_list = response.context_data['object_list']
        self.assertIn(self.note, object_list)

    def test_note_in_list_not_author(self):
        """Поверяет попадание заметок в список на чужую страницу."""
        self.client.force_login(self.not_author)
        response = self.client.get(self.list_url)
        object_detail = response.context_data['object_list']
        self.assertNotIn(self.note, object_detail)

    def test_authorized_client_has_add_and_edit_form(self):
        """Проверяет передачу формы на страницы создания и редактирования."""
        self.client.force_login(self.author)
        for url in (self.add_url, self.edit_url):
            with self.subTest():
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
