from django import forms
from .models import Post, Group

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Напишите что-нибудь...',
            'group': 'Выберите группу (необязательно)',
        }

