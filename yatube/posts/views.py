from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import paginate


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    context = {
        'page_obj': paginate(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'posts': post_list,
        'page_obj': paginate(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.post_set.all()
    context = {
        'author': author,
        'page_obj': paginate(request, post_list),
        'posts': post_list,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    full_post = get_object_or_404(Post, id=post_id)
    context = {
        'full_post': full_post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method != 'POST':
        form = PostForm()
        context = {'form': form}
        return render(request, template, context)

    form = PostForm(request.POST)
    if not form.is_valid():
        context = {'form': form}
        return render(request, template, context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author.username)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)

    if request.method != "POST":
        form = PostForm(instance=post)
        context = {'form': form}
        return render(request, template, context)

    form = PostForm(request.POST, instance=post)
    if not form.is_valid():
        context = {'form': form}
        return render(request, template, context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id)
