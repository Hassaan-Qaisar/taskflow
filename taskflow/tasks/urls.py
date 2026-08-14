# tasks/urls.py
from django.urls import path
from .views import TaskDetailView

app_name = "tasks"

urlpatterns = [
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
]