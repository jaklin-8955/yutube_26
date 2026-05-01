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

from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост для модели',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_public_pages_accessible(self):
        """Публичные страницы доступны любому пользователю."""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    #
    def test_create_page_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        url = reverse('posts:post_create')
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_author_only(self):
        """Страница редактирования поста доступна только автору."""
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})

        
        response = self.author_client.get(edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        
        response = self.authorized_client.get(edit_url)
        expected_url = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        self.assertRedirects(response, expected_url)

        response = self.guest_client.get(edit_url)
        self.assertRedirects(response, f'/auth/login/?next={edit_url}')

    def test_create_redirect_anonymous(self):
        """Неавторизованный перенаправляется с /create/ на логин."""
        url = reverse('posts:post_create')
        response = self.guest_client.get(url)
        self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_404_page(self):
        """Запрос к несуществующей странице возвращает 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_use_correct_templates(self):
        """URL‑адреса используют ожидаемые шаблоны."""
        templates_urls = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile', kwargs={'username': self.author.username}),
            'posts/post_detail.html': reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        templates_urls['posts/create_post.html (edit)'] = edit_url

        for template, url in templates_urls.items():
            with self.subTest(url=url):
                response = self.author_client.get(url) if 'edit' in template else self.authorized_client.get(url)
                self.assertTemplateUsed(response, template.split(' (')[0])