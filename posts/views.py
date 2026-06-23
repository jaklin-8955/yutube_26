from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Post, Group
from .forms import PostForm

User = get_user_model()


def index(request):
    """Главная страница с пагинацией (10 постов)"""
    post_list = Post.objects.select_related('author', 'group').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    """Страница группы с пагинацией (10 постов)"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'group': group, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Профайл пользователя с пагинацией (10 постов)"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_count': post_list.count(),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница отдельного поста"""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id
    )
    posts_count = post.author.posts.count()
    context = {
        'post': post,
        'posts_count': posts_count,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание нового поста"""
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {'form': form, 'is_edit': False}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Редактирование поста (только для автора)"""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/create_post.html', context)