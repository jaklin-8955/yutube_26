from django import forms
from .models import Post, Comment  # объедините импорты

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }
        help_texts = {
            'text': 'Напишите что-нибудь...',
            'group': 'Выберите группу (необязательно)',
            'image': 'Загрузите изображение (необязательно)',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',) 