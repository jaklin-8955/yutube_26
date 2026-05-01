from django.test import TestCase


from django.test import TestCase, Client
from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_pages_accessible(self):
        urls = ['/about/author/', '/about/tech/']
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
