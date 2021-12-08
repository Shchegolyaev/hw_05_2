from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix="index_page")
def index(request):
    post = Post.objects.select_related('author').all()
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post = group.posts.all()
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group,
                  'post': post, 'page': page})


def profile(request, username):
    following = False
    user = get_object_or_404(User, username=username)
    post = user.posts.all()
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if not request.user.is_anonymous and Follow.objects.filter(
            user=request.user, author=user).exists():
        following = True
    return render(request, 'profile.html', {
                  'author': user,
                  'following': following,
                  'post': post,
                  'page': page})


def post_view(request, username, post_id):
    following = False
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    if not request.user.is_anonymous and Follow.objects.filter(
            user=request.user, author=user).exists():
        following = True
    return render(request, 'post.html', {
        'add_comment': True,
        'comments': comments,
        'form': form,
        'following': following,
        "author": user,
        'post': post
    })


@login_required
@csrf_exempt
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('index')
        return render(request, 'form.html', {'form': form})

    form = PostForm()
    return render(request, 'form.html', {'form': form})


@csrf_exempt
def post_edit(request, username, post_id):
    if username != request.user.username:
        return redirect(reverse('post', args=(username, post_id)))
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'form.html', {
        'edit': True,
        'post': post,
        'form': form
    })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post', username, post_id)
        return render(request, 'includes/comments.html', {'form': form})

    form = CommentForm()
    return render(request, 'includes/comments.html', {
        'form': form})


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
                  'post': post,
                  'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
