from django.urls import path

from . import views

app_name = "marketing"

urlpatterns = [
    path("", views.home, name="home"),
    path("problem/", views.problem, name="problem"),
    path("solution/", views.solution, name="solution"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("pricing/", views.pricing, name="pricing"),
    path("business/", views.business, name="business"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("careers/", views.careers, name="careers"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("contact/", views.contact, name="contact"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
]
