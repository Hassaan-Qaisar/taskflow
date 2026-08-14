# tasks/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView

from .models import Task


class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return task.project.owner_id == user.id or task.assigned_to.filter(id=user.id).exists()