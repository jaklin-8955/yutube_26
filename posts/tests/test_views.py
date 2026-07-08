from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from http import HTTPStatus
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
            description='Описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group
        )
        cls.other_group = Group.objects.create(
            title='Другая группа',
            slug='other-slug',
            description='Другая группа'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

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
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_edit_only_authorized(self):
        """Страницы создания и редактирования поста доступны только авторизованным."""
        create_url = reverse('posts:post_create')
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})

        response = self.guest_client.get(create_url)
        self.assertRedirects(response, f'/auth/login/?next={create_url}')

        response = self.guest_client.get(edit_url)
        self.assertRedirects(response, f'/auth/login/?next={edit_url}')

        response = self.authorized_client.get(create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.authorized_client.get(edit_url)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        response = self.author_client.get(edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_use_correct_templates(self):
        """Проверка, что view-функции используют ожидаемые шаблоны."""
        templates_urls = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile', kwargs={'username': self.author.username}),
            'posts/post_detail.html': reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/create_post.html': reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        for template, url in templates_urls.items():
            with self.subTest(url=url):
                if 'create' in url or 'edit' in url:
                    client = self.author_client
                else:
                    client = self.guest_client
                response = client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_uses_correct_template_and_context(self):
        """Главная страница использует correct template и передаёт page_obj."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertTemplateUsed(response, 'posts/index.html')
        self.assertIn('page_obj', response.context)
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

    def test_post_detail_context(self):
        """Страница деталей поста передаёт правильный пост."""
        response = self.guest_client.get(reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'], self.post)

    def test_create_post_context(self):
        """На страницу создания поста передаётся форма."""
        response = self.author_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)

    def test_pagination_on_index(self):
        """На главной странице пагинатор выводит 10 постов на первой странице и 3 на второй."""
        for i in range(12):
            Post.objects.create(
                text=f'Пост номер {i}',
                author=self.author
            )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_pagination_on_profile(self):
        """На странице профайла пагинатор работает аналогично."""
        for i in range(12):
            Post.objects.create(
                text=f'Пост автора {i}',
                author=self.author
            )
        url = reverse('posts:profile', kwargs={'username': self.author.username})
        response = self.guest_client.get(url)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.guest_client.get(url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

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
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count_before + 1)
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, self.group)
        self.assertEqual(new_post.author, self.user)
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
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, old_text)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

    def test_post_with_group_appears_in_correct_pages(self):
        """Если при создании поста указать группу, он появляется на главной, в группе, в профайле,
        и не появляется в другой группе."""
        form_data = {
            'text': 'Пост с группой',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        new_post = Post.objects.get(text='Пост с группой')
        self.assertEqual(new_post.group, self.group)

        index_response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(new_post, index_response.context['page_obj'].object_list)

        group_response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn(new_post, group_response.context['page_obj'].object_list)

        profile_response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertIn(new_post, profile_response.context['page_obj'].object_list)

        other_group_response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.other_group.slug})
        )
        self.assertNotIn(new_post, other_group_response.context['page_obj'].object_list)