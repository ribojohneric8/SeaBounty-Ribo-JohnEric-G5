from django.urls import path

from . import views

app_name = "stalls"

urlpatterns = [
    path("", views.stall_list, name="list"),
    path("mine/", views.my_stalls, name="mine"),
    path("new/", views.stall_create, name="create"),
    path("<int:pk>/", views.stall_detail, name="detail"),
    path("<int:pk>/edit/", views.stall_edit, name="edit"),
    path("<int:pk>/delete/", views.stall_delete, name="delete"),
]
