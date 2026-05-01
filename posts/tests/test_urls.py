from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(slug='test')
        cls.post = Post.objects.create(text='text', author=cls.user, group=cls.group)

    def setUp(self):
        self.guest = Client()
        self.auth = Client()
        self.auth.force_login(self.user)

    def test_urls_accessible(self):
        """Проверка доступности URL для анонимного пользователя."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        for url in urls:
            response = self.guest.get(url)
            self.assertEqual(response.status_code, 200)

    def test_edit_create_redirect_anonymous(self):
        """Аноним перенаправляется с /create/ и /edit/ на логин."""
        create = reverse('posts:post_create')
        edit = reverse('posts:post_edit', args=[self.post.id])
        response = self.guest.get(create)
        self.assertRedirects(response, f'/auth/login/?next={create}')
        response = self.guest.get(edit)
        self.assertRedirects(response, f'/auth/login/?next={edit}')

    def test_edit_create_authenticated(self):
        """Авторизованный может открыть /create/, но не чужой /edit/."""
        response = self.auth.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 200)
        
        another_user = User.objects.create_user(username='another')
        self.auth.force_login(another_user)
        edit = reverse('posts:post_edit', args=[self.post.id])
        response = self.auth.get(edit)
       
        self.assertRedirects(response, reverse('posts:post_detail', args=[self.post.id]))