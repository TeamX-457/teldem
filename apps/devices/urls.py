from django.urls import path

from . import views

app_name = "devices"

urlpatterns = [
    path("", views.device_list, name="list"),
    path("register/", views.device_register, name="register"),
    path("<int:pk>/", views.device_detail, name="detail"),
    path("<int:pk>/edit/", views.device_update, name="update"),
    path("<int:pk>/toggle-armed/", views.device_toggle_armed, name="toggle_armed"),
    path("<int:pk>/delete/", views.device_delete, name="delete"),
]
