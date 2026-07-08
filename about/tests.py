from django.test import TestCase, Client
from http import HTTPStatus   


class AboutURLTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_pages_accessible(self):
        """Страницы about доступны любому пользователю."""
        urls = ['/about/author/', '/about/tech/']
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_use_correct_templates(self):
        """Страницы about используют ожидаемые шаблоны."""
        url_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)