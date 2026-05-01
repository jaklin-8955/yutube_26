from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост для модели',
            author=cls.user,
            group=cls.group
        )

    def test_group_str_returns_title(self):
        """__str__ группы возвращает её название."""
        self.assertEqual(str(self.group), self.group.title)

    def test_post_str_returns_first_15_symbols(self):
        """__str__ поста возвращает первые 15 символов текста."""
        expected = self.post.text[:15]
        self.assertEqual(str(self.post), expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Напишите что-нибудь...',
            'group': 'Необязательное поле',
        }
        for field, expected in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected
                )

    def test_ordering(self):
        """Посты сортируются по убыванию даты (сначала новые)."""
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user,
            pub_date=timezone.now()
        )
        old_post = Post.objects.create(
            text='Старый пост',
            author=self.user,
            pub_date=timezone.now() - timedelta(days=10)
        )
        posts = list(Post.objects.all().order_by('-pub_date'))
        self.assertEqual(posts[0], new_post)
        self.assertEqual(posts[1], old_post)