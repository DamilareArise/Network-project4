import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import User, Post, Follow


def index(request):
    posts = Post.objects.all().order_by("-timestamp")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(request.user.liked_posts.values_list("id", flat=True))

    return render(request, "network/index.html", {
        "page_obj": page_obj,
        "liked_post_ids": liked_post_ids,
    })


@login_required
def new_post(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Post.objects.create(user=request.user, content=content)
    return HttpResponseRedirect(reverse("index"))


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = profile_user.posts.all().order_by("-timestamp")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    following_count = Follow.objects.filter(follower=profile_user).count()
    followers_count = Follow.objects.filter(following=profile_user).count()

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()

    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(request.user.liked_posts.values_list("id", flat=True))

    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "following_count": following_count,
        "followers_count": followers_count,
        "is_following": is_following,
        "liked_post_ids": liked_post_ids,
    })


@login_required
def follow_toggle(request, username):
    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)
        if target_user != request.user:
            existing = Follow.objects.filter(follower=request.user, following=target_user)
            if existing.exists():
                existing.delete()
            else:
                Follow.objects.create(follower=request.user, following=target_user)
    return HttpResponseRedirect(reverse("profile", args=[username]))


@login_required
def following(request):
    following_ids = Follow.objects.filter(follower=request.user).values_list("following", flat=True)
    posts = Post.objects.filter(user__in=following_ids).order_by("-timestamp")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    liked_post_ids = set(request.user.liked_posts.values_list("id", flat=True))

    return render(request, "network/following.html", {
        "page_obj": page_obj,
        "liked_post_ids": liked_post_ids,
    })


@csrf_exempt
@login_required
def like_post(request, post_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"likes": post.likes.count(), "liked": liked})


@csrf_exempt
@login_required
def delete_post(request, post_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE request required."}, status=400)

    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return JsonResponse({"error": "You can only delete your own posts."}, status=403)

    post.delete()
    return JsonResponse({"message": "Post deleted."})


@csrf_exempt
@login_required
def edit_post(request, post_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)

    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return JsonResponse({"error": "You can only edit your own posts."}, status=403)

    data = json.loads(request.body)
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Content cannot be empty."}, status=400)

    post.content = content
    post.save()
    return JsonResponse({"content": post.content})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
