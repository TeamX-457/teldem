from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_overview, name="overview"),
    path("subscribe/<slug:slug>/", views.plan_subscribe, name="subscribe"),
]
