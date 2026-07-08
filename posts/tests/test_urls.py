from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus   
from django.urls import reverse
from posts.models import Group, Post


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
       
        cls.user = User.objects.create_user(username='author')
       
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
       
        cls.post = Post.objects.create(
            text='Тестовый пост для URL-тестов',
            author=cls.user,
            group=cls.group
        )
       
        cls.other_user = User.objects.create_user(username='not_author')

    def setUp(self):
       
        self.guest_client = Client()
       
        self.author_client = Client()
        self.author_client.force_login(self.user)
       
        self.other_client = Client()
        self.other_client.force_login(self.other_user)

  

    def test_public_pages_accessible_for_anyone(self):
        """Публичные страницы доступны любому пользователю (включая анонимов)."""
        public_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_pages_accessible_for_authorized(self):
        """Страницы создания и редактирования поста доступны авторизованному пользователю."""
        private_urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        for url in private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_author_only(self):
        """Страница редактирования поста доступна только автору."""
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        
        response = self.other_client.get(edit_url)
       
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_private_pages_redirect_anonymous(self):
        """Приватные страницы перенаправляют анонимного пользователя на логин."""
        private_urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        login_url = reverse('users:login')
        for url in private_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                expected_redirect = f'{login_url}?next={url}'
                self.assertRedirects(response, expected_redirect)

   

    def test_urls_use_correct_templates(self):
        """URL-адреса используют ожидаемые HTML-шаблоны."""
       
        url_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): 'posts/create_post.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    

    def test_unexisting_page_returns_404(self):
        """Запрос к несуществующей странице возвращает код 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)