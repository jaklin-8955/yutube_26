
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class UsersURLTests(TestCase):
    def setUp(self):
        
        self.guest_client = Client()

    def test_users_pages_accessible(self):
        """Страницы регистрации, входа и выхода доступны анонимному пользователю."""
        urls = [
            reverse('users:login'),
            reverse('users:logout'),
            reverse('users:signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_pages_use_correct_templates(self):
        """Страницы users используют ожидаемые шаблоны."""
        
        url_templates = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)



def test_signup_creates_new_user(self):
    """При валидной регистрации создаётся новый пользователь."""
    users_count_before = User.objects.count()
    form_data = {
        'username': 'newuser',
        'password1': 'Nesterova8955',
        'password2': 'Nesterova8955',
        'email': 'jaklin2555@yandex.ru',
    }
    response = self.client.post(
        reverse('users:signup'),
        data=form_data,
        follow=True
    )
    self.assertEqual(response.status_code, HTTPStatus.OK)
    self.assertEqual(User.objects.count(), users_count_before + 1)
    new_user = User.objects.get(username='newuser')
    self.assertEqual(new_user.email, form_data['email'])
    self.assertRedirects(response, reverse('posts:index'))  
