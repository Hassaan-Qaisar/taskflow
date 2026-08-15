# tasks/urls.py
from django.urls import path
from .views import TaskDetailView, TaskUpdateView

app_name = "tasks"

urlpatterns = [
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="edit"),
]