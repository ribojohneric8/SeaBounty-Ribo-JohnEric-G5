from django.urls import path

from . import views

app_name = "catches"

urlpatterns = [
    path("", views.catch_list, name="list"),
    path("mine/", views.my_updates, name="mine"),
    path("new/", views.catch_create, name="create"),
    path("<int:pk>/edit/", views.catch_edit, name="edit"),
    path("<int:pk>/delete/", views.catch_delete, name="delete"),
]
