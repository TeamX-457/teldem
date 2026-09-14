from django.urls import path

from . import views

app_name = "alerts"

urlpatterns = [
    path("", views.alert_inbox, name="inbox"),
    path("<int:pk>/resolve/", views.alert_resolve, name="resolve"),
]
