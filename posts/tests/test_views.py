import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTests(TestCase):
    """Тесты для проверки передачи картинок в контекст и создания постов с картинкой."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        cls.image = SimpleUploadedFile(
            name='test_image.gif',
            content=b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Пост с картинкой',
            author=cls.user,
            group=cls.group,
            image=cls.image
        )

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_image_in_context_on_index(self):
        """Картинка передаётся в контекст на главной странице."""
        response = self.client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'На главной картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_profile(self):
        """Картинка передаётся в контекст на странице профайла."""
        response = self.client.get(reverse('posts:profile', args=[self.user.username]))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'В профайле картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_group(self):
        """Картинка передаётся в контекст на странице группы."""
        response = self.client.get(reverse('posts:group_list', args=[self.group.slug]))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'В группе картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_detail(self):
        """Картинка передаётся в контекст на отдельной странице поста."""
        response = self.client.get(reverse('posts:post_detail', args=[self.post.id]))
        post_from_context = response.context['post']
        self.assertTrue(post_from_context.image, 'На детальной странице картинка отсутствует в контексте')
        self.assertEqual(post_from_context.image.name, 'posts/test_image.gif')

    def test_create_post_with_image(self):
        """При отправке поста с картинкой через форму создаётся запись в БД."""
        self.client.force_login(self.user)
        new_image = SimpleUploadedFile(
            name='new_image.gif',
            content=b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост с картинкой',
            'group': self.group.id,
            'image': new_image,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 2)
        new_post = Post.objects.latest('id')
        self.assertTrue(new_post.image.name.startswith('posts/new_image'))
        self.assertRedirects(response, reverse('posts:profile', args=[self.user.username]))


class CommentTests(TestCase):
    """Тесты для системы комментариев."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.post = Post.objects.create(
            text='Тестовый пост для комментариев',
            author=cls.user
        )

    def setUp(self):
        cache.clear()

    def test_anonymous_cant_comment(self):
        """Неавторизованный пользователь не может комментировать."""
        url = reverse('posts:add_comment', args=[self.post.id])
        response = self.client.post(url, {'text': 'Анонимный комментарий'})
        expected_redirect = f'/auth/login/?next={url}'
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authorized_user_can_comment(self):
        """Авторизованный пользователь может комментировать."""
        self.client.login(username='testuser', password='testpass')
        url = reverse('posts:add_comment', args=[self.post.id])
        response = self.client.post(url, {'text': 'Отличный пост!'}, follow=True)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Отличный пост!')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

        detail_url = reverse('posts:post_detail', args=[self.post.id])
        response = self.client.get(detail_url)
        self.assertContains(response, 'Отличный пост!')
        self.assertContains(response, self.user.username)


class CacheTests(TestCase):
    """Тесты для проверки кеширования главной страницы."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser')
        cls.post = Post.objects.create(
            text='Тестовый пост для кеша',
            author=cls.user
        )

    def setUp(self):
        cache.clear()

    def test_index_cache_used(self):
        """Проверяем, что главная страница кешируется."""
        url = reverse('posts:index')
        
        with self.assertNumQueries(2):
            response1 = self.client.get(url)
       
        with self.assertNumQueries(0):
            response2 = self.client.get(url)
        self.assertEqual(response1.content, response2.content)

    def test_index_cache_key_prefix(self):
        """Проверяем, что в кеше используется префикс 'index_page'."""
        url = reverse('posts:index')
        self.client.get(url)
        cache_keys = cache._cache.keys()
        found = any('index_page' in key for key in cache_keys)
        self.assertTrue(found, 'Ключ кеша с префиксом index_page не найден')

    def test_cache_after_post_deletion(self):
        """При удалении поста он остаётся в кеше до очистки."""
        url = reverse('posts:index')
        response_before = self.client.get(url)
        content_before = response_before.content

        # Удаляем пост
        self.post.delete()

       
        response_after_delete = self.client.get(url)
        content_after_delete = response_after_delete.content
        self.assertEqual(content_before, content_after_delete)

     
        cache.clear()
        response_after_clear = self.client.get(url)
        content_after_clear = response_after_clear.content
        self.assertNotEqual(content_before, content_after_clear)


class FollowTests(TestCase):
    """Тесты для системы подписок."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Пост автора',
            author=cls.author
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow_unfollow(self):
        """Авторизованный пользователь может подписываться и отписываться."""
        follow_count = Follow.objects.count()

       
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

        
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[self.author.username])
        )
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_follow_index(self):
        """Новый пост появляется в ленте подписанных."""
        
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, self.post.text)

        
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[self.author.username])
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)

    def test_new_post_not_in_feed_if_not_followed(self):
        """Новый пост не появляется в ленте, если не подписан на автора."""
        new_author = User.objects.create_user(username='new_author')
        new_post = Post.objects.create(
            text='Новый пост другого автора',
            author=new_author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, new_post.text)

    def test_following_flag_in_profile(self):
        """На странице профиля передаётся флаг following."""
        
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.author.username])
        )
        self.assertFalse(response.context['following'])

       
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.author.username])
        )
        self.assertTrue(response.context['following'])


class ErrorPagesTests(TestCase):
    """Тесты для кастомных страниц ошибок."""

    def test_404_custom(self):
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')