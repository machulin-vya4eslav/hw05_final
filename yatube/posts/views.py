from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_page_context


TIME_OF_CACHE = 20


def index(request):
    title = 'Последние обновления на сайте'

    post_list = Post.objects.all()
    page_obj = get_page_context(post_list, request)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
        'title': title
    }

    if not cache.get('index_page'):
        cache.set('index_page', context, TIME_OF_CACHE)
    else:
        context = cache.get('index_page')

    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    title = f'Записи сообщества {group}'
    group_post_list = group.posts.all()
    page_obj = get_page_context(group_post_list, request)

    template = 'posts/group_list.html'
    context = {
        'group': group,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    title = f'Профайл пользователя {author.get_full_name()}'
    author_post_list = author.posts.all()
    page_obj = get_page_context(author_post_list, request)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )

    template = 'posts/profile.html'
    context = {
        'title': title,
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    form = CommentForm()

    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


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
    form = PostForm(request.POST or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)

    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id)

    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_context(posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.get_username() != username:
        Follow.objects.create(
            user=request.user,
            author=User.objects.get(username=username)
        )
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    if request.user.get_username() != username:
        Follow.objects.get(
            user=request.user,
            author=User.objects.get(username=username)
        ).delete()
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)
