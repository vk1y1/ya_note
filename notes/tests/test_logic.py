"""Тестирование логики проекта YaNotes."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тестирование страниц создания отельной заметки."""

    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'note_slug'

    @classmethod
    def setUpTestData(cls):
        """Фикстуры для теста логики создания заметки."""
        cls.url = reverse('notes:add')
        cls.url_siccess = reverse('notes:success')
        cls.login_url = reverse('users:login')
        cls.user = User.objects.create(username='Автор_1')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG}

    def test_anonymous_user_cant_create_note(self):
        """Поверяет невозможность создания заметки анонимным пользователем."""
        response = self.client.post(self.url, data=self.form_data)
        expected_url = f'{self.login_url}?next={self.url}'
        self.assertRedirects(response, f'{expected_url}')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Поверяет возможность создания заметки залогиненным пользователем."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f'{self.url_siccess}')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_user_cant_use_repeating_slug(self):
        """Поверяет невозможность создать две заметки с одинаковым slug."""
        self.note = Note.objects.create(
            title='Заголовок_1', text='Текст', slug='slug', author=self.user)
        repeating_slug_note = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'slug'
        }
        response = self.auth_client.post(self.url, data=repeating_slug_note)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=f'{self.note.slug}' + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        """Поверяет возможность создать заметки с незаполненным slug."""
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        assert new_note.slug == expected_slug


class TestNoteEditDelete(TestCase):
    """Тестирование страниц редактирования и удаления отельной заметки."""

    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug'
    NEW_NOTE_TITLE = 'Обновлённый заголовок'
    NEW_NOTE_TEXT = 'Обновлённая заметка'
    NEW_NOTE_SLUG = 'new_slug'

    @classmethod
    def setUpTestData(cls):
        """Фикстуры для теста логики редактирования и удаления заметки."""
        cls.author = User.objects.create(username='Автор_1')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_author = User.objects.create(username='Автор_2')
        cls.another_author_client = Client()
        cls.another_author_client.force_login(cls.another_author)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG
        }

    def test_author_can_delete_note(self):
        """Поверяет возможность удаления заметки автором."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_author(self):
        """Поверяет невозможность удаления заметки не автором."""
        response = self.another_author_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Поверяет возможность редактирования заметки автором."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(
            (self.note.title, self.note.text, self.note.slug),
            (self.NEW_NOTE_TITLE, self.NEW_NOTE_TEXT, self.NEW_NOTE_SLUG)
        )

    def test_user_cant_edit_note_of_another_user(self):
        """Поверяет невозможность редактирования заметки не автором."""
        response = self.another_author_client.post(
            self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(
            (self.note.title, self.note.text, self.note.slug),
            (self.NOTE_TITLE, self.NOTE_TEXT, self.NOTE_SLUG)
        )
