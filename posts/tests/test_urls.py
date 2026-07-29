from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )
        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.user)

    def setUp(self):
        cache.clear()

    def test_public_pages_accessible_for_anyone(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:post_detail', args=[self.post.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_private_pages_accessible_for_authorized(self):
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_private_pages_redirect_anonymous(self):
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                expected_url = f'/auth/login/?next={url}'
                self.assertRedirects(response, expected_url)

    def test_urls_use_correct_templates(self):
        templates = [
            ('posts:index', 'posts/index.html'),
            ('posts:group_list', 'posts/group_list.html'),
            ('posts:profile', 'posts/profile.html'),
            ('posts:post_detail', 'posts/post_detail.html'),
            ('posts:post_create', 'posts/create_post.html'),
            ('posts:post_edit', 'posts/create_post.html'),
        ]
        for name, template in templates:
            with self.subTest(name=name):
                if name == 'posts:post_edit':
                    url = reverse(name, args=[self.post.id])
                elif name == 'posts:group_list':
                    url = reverse(name, args=[self.group.slug])
                elif name == 'posts:profile':
                    url = reverse(name, args=[self.user.username])
                elif name == 'posts:post_detail':
                    url = reverse(name, args=[self.post.id])
                else:
                    url = reverse(name)
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)