from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.billing.models import SubscriptionPlan

from .forms import ContactForm
from .models import BlogPost


def home(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)[:4]
    posts = BlogPost.objects.filter(is_published=True)[:3]
    return render(request, "marketing/home.html", {"plans": plans, "posts": posts})


def problem(request):
    return render(request, "marketing/problem.html")


def solution(request):
    return render(request, "marketing/solution.html")


def how_it_works(request):
    return render(request, "marketing/how_it_works.html")


def pricing(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, "marketing/pricing.html", {"plans": plans})


def business(request):
    return render(request, "marketing/business.html")


def about(request):
    return render(request, "marketing/about.html")


def faq(request):
    return render(request, "marketing/faq.html")


def careers(request):
    return render(request, "marketing/careers.html")


def privacy(request):
    return render(request, "marketing/privacy.html")


def terms(request):
    return render(request, "marketing/terms.html")


def contact(request):
    interest = request.GET.get("interest")
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thanks for reaching out! A TELDEM specialist will contact you within "
                "one business day.",
            )
            return redirect("marketing:contact")
    else:
        initial = {}
        if interest in ("b2c", "b2b"):
            initial["interest_type"] = interest
        form = ContactForm(initial=initial)

    return render(request, "marketing/contact.html", {"form": form})


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    return render(request, "marketing/blog_list.html", {"posts": posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    other_posts = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    return render(
        request, "marketing/blog_detail.html", {"post": post, "other_posts": other_posts}
    )
