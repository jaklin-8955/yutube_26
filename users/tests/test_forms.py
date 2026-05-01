
from django.test import TestCase
from users.forms import CreationForm

class CreationFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'Жаклин',
            'last_name': 'Нестерова',
            'email': 'jaklin2555@yandex.ru',
            'password1': 'Str0ngP@ss',
            'password2': 'Str0ngP@ss',
        }
        form = CreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_username(self):
        form_data = {
            'first_name': 'Жаклин',
            'last_name': 'Нестерова',
            'email': 'jaklin2555@yandex.ru',
            'password1': 'Str0ngP@ss',
            'password2': 'Str0ngP@ss',
        }
        form = CreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
