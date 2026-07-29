import shutil
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_image_in_context_on_index(self):
        response = self.client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'На главной картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_profile(self):
        response = self.client.get(reverse('posts:profile', args=[self.user.username]))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'В профайле картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_group(self):
        response = self.client.get(reverse('posts:group_list', args=[self.group.slug]))
        first_post = response.context['page_obj'][0]
        self.assertTrue(first_post.image, 'В группе картинка отсутствует в контексте')
        self.assertEqual(first_post.image.name, 'posts/test_image.gif')

    def test_image_in_context_on_detail(self):
        response = self.client.get(reverse('posts:post_detail', args=[self.post.id]))
        post_from_context = response.context['post']
        self.assertTrue(post_from_context.image, 'На детальной странице картинка отсутствует в контексте')
        self.assertEqual(post_from_context.image.name, 'posts/test_image.gif')

    def test_create_post_with_image(self):
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
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.post = Post.objects.create(
            text='Тестовый пост для комментариев',
            author=cls.user
        )

    def test_anonymous_cant_comment(self):
        """Неавторизованный пользователь не может отправить комментарий."""
        url = reverse('posts:add_comment', args=[self.post.id])
        response = self.client.post(url, {'text': 'Анонимный комментарий'})
        expected_redirect = f'/auth/login/?next={url}'
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authorized_user_can_comment(self):
        """Авторизованный пользователь может оставить комментарий."""
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