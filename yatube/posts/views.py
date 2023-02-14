from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_page_context


TIME_OF_CACHE = 20


@cache_page(TIME_OF_CACHE, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    page_obj = get_page_context(post_list, request)
    context = {
        'page_obj': page_obj,
        'title': 'Последние обновления на сайте'
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_post_list = group.posts.all()
    page_obj = get_page_context(group_post_list, request)
    context = {
        'group': group,
        'title': f'Записи сообщества {group}',
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_post_list = author.posts.all()
    page_obj = get_page_context(author_post_list, request)

    context = {
        'title': f'Профайл пользователя {author.get_full_name()}',
        'page_obj': page_obj,
        'author': author
    }

    context.update(
        following=request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)

    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_context(posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.get_username() != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    if request.user.get_username() != username:
        Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
        ).delete()
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)
