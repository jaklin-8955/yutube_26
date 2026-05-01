from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    # --- Smoke тесты: проверка доступности страниц ---
    def test_pages_accessible_for_anonymous(self):
        """Главная, страница группы, профайл, детали поста доступны анониму."""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_create_edit_only_authorized(self):
        """Страницы создания и редактирования поста доступны авторизованным."""
        create_url = reverse('posts:post_create')
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})

        # Аноним → редирект на логин
        response = self.guest_client.get(create_url)
        self.assertRedirects(response, f'/auth/login/?next={create_url}')

        response = self.guest_client.get(edit_url)
        self.assertRedirects(response, f'/auth/login/?next={edit_url}')

        # Авторизованный (не автор) может зайти на create, но на edit – редирект на детали
        response = self.authorized_client.get(create_url)
        self.assertEqual(response.status_code, 200)

        response = self.authorized_client.get(edit_url)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        # Автор может редактировать
        response = self.author_client.get(edit_url)
        self.assertEqual(response.status_code, 200)

    # --- Проверка контекста (пагинация) ---
    def test_index_uses_correct_template_and_context(self):
        """Главная страница использует correct template и передаёт page_obj."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertTemplateUsed(response, 'posts/index.html')
        self.assertIn('page_obj', response.context)
        # Проверяем, что пагинатор выводит 10 постов (если их >10, но для теста создадим 11)
        # Для простоты проверим, что object_list существует
        self.assertTrue(hasattr(response.context['page_obj'], 'object_list'))

    def test_profile_uses_correct_context(self):
        """Страница профайла передаёт автора и page_obj."""
        response = self.guest_client.get(reverse('posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(response.context['author'], self.author)
        self.assertIn('page_obj', response.context)

    def test_group_list_uses_correct_context(self):
        """Страница группы передаёт группу и page_obj."""
        response = self.guest_client.get(reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)

    # --- Проверка создания поста ---
    def test_post_creation_by_authorized_user(self):
        """Авторизованный пользователь может создать пост."""
        post_count_before = Post.objects.count()
        form_data = {
            'text': 'Созданный пост через тест',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), post_count_before + 1)
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, self.group)
        self.assertEqual(new_post.author, self.user)
        # Редирект на профайл пользователя
        self.assertRedirects(response, reverse('posts:profile', kwargs={'username': self.user.username}))

    def test_post_edit_by_author(self):
        """Автор может отредактировать свой пост."""
        old_text = self.post.text
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, old_text)
        self.assertEqual(self.post.text, form_data['text'])
        # Редирект на страницу деталей поста
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

    # --- Проверка пагинации (на главной странице) ---
    def test_pagination_on_index(self):
        """На главной странице пагинатор выводит 10 постов."""
        # Создадим 12 постов одним автором
        for i in range(12):
            Post.objects.create(
                text=f'Пост номер {i}',
                author=self.author
            )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)  

      