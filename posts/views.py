from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Post, Group
from .forms import PostForm

User = get_user_model()


def index(request):
   
    post_list = Post.objects.select_related('author', 'group').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'group': group, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'author': author, 'page_obj': page_obj}
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
   
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id
    )
    return render(request, 'posts/post_detail.html', {'post': post})


@login_required
def post_create(request):
   
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)

from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Post, Group

def profile(request, username):
    # Получаем автора по username
    author = get_object_or_404(User, username=username)
    # Все посты автора, отсортированные по дате (сначала новые)
    posts = author.posts.all().order_by('-pub_date')
    # Пагинация: 10 постов на страницу
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Количество всех постов автора
    count = posts.count()
    context = {
        'author': author,
        'page_obj': page_obj,
        'count': count,
    }
    return render(request, 'posts/profile.html', context)

def post_detail(request, post_id):
    # Получаем пост или 404
    post = get_object_or_404(Post, id=post_id)
    # Количество постов автора
    count = post.author.posts.count()
    context = {
        'post': post,
        'count': count,
    }
    return render(request, 'posts/post_detail.html', context)

from django.http import HttpResponse

def group_posts(request, slug):
    return HttpResponse(f"Страница группы {slug} (заглушка)")