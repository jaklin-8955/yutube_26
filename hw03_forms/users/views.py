from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'

from .forms import CreationForm   # вместо стандартной UserCreationForm

class SignUp(CreateView):
    form_class = CreationForm     # ← обязательно
    template_name = 'users/signup.html'
    success_url = reverse_lazy('users:login')