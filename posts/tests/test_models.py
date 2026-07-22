
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
            text='Тестовый пост для проверки __str__',
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
       
        self.assertEqual(str(self.group), self.group.title)
       
        self.assertEqual(str(self.post), self.post.text[:15])

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_ordering(self):
        """Посты сортируются по убыванию даты (сначала новые)."""
      
        Post.objects.all().delete()

       
        old_post = Post.objects.create(
            text='Старый пост',
            author=self.user,
        )
        old_post.pub_date = timezone.now() - timedelta(days=10)
        old_post.save()

        
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user,
        )

        
        posts = list(Post.objects.all().order_by('-pub_date'))
        self.assertEqual(posts[0], new_post, "Новый пост должен быть первым")
        self.assertEqual(posts[1], old_post, "Старый пост должен быть вторым")