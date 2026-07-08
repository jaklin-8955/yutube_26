from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from users.forms import CreationForm


class CreationFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'Жаклин',
            'last_name': 'Нестерова',
            'email': 'jaklin2555@yandex.ru',
            'password1': 'Str0ngP@ss',
            'password2': 'Str0ngP@ss',
        }
        form = CreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_username(self):
        form_data = {
            'first_name': 'Жаклин',
            'last_name': 'Нестерова',
            'email': 'jaklin2555@yandex.ru',
            'password1': 'Str0ngP@ss',
            'password2': 'Str0ngP@ss',
        }
        form = CreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class UsersURLTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_and_signup_accessible(self):
        """Страницы входа и регистрации доступны всем."""
        urls = [
            reverse('users:login'),
            reverse('users:signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_redirects(self):
        """Страница выхода перенаправляет (статус 302)."""
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_login_and_signup_templates(self):
        """Страницы входа и регистрации используют правильные шаблоны."""
        url_templates = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)

    def test_signup_context_has_form(self):
        """На страницу регистрации в контексте передаётся форма."""
        response = self.client.get(reverse('users:signup'))
        self.assertIn('form', response.context)
       
        self.assertTrue(hasattr(response.context['form'], 'is_valid'))