from django.test import TestCase
from django.contrib.auth import get_user_model
from posts.models import Group, Post
from posts.forms import PostForm

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

    def test_create_post_valid_data(self):
        """Валидная форма создаёт пост."""
        form_data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

        post = form.save(commit=False)
        post.author = self.user
        post.save()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().text, form_data['text'])
        self.assertEqual(Post.objects.first().group, self.group)

    def test_create_post_without_group(self):
        """Форма валидна, если группа не указана (blank=True)."""
        form_data = {'text': 'Пост без группы'}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_create_post_empty_text_not_valid(self):
        """Форма невалидна, если поле text пустое."""
        form_data = {'text': ''}
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_edit_post(self):
        """Форма редактирования поста работает."""
        post = Post.objects.create(
            text='Старый текст',
            author=self.user,
            group=self.group
        )
        form_data = {
            'text': 'Новый отредактированный текст',
            'group': self.group.id,
        }
        form = PostForm(data=form_data, instance=post)
        self.assertTrue(form.is_valid())
        form.save()
        post.refresh_from_db()
        self.assertEqual(post.text, form_data['text'])


