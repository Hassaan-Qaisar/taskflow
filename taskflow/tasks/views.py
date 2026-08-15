# tasks/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from projects.models import ProjectMembership

from .forms import TaskOwnerUpdateForm, TaskStatusUpdateForm
from .models import Task


class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return task.project.owner_id == user.id or task.assigned_to_id == user.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        user = self.request.user
        context["can_manage_task"] = task.project.owner_id == user.id
        context["can_update_status"] = task.assigned_to_id == user.id
        return context


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    template_name = "tasks/task_form.html"
    context_object_name = "task"

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return task.project.owner_id == user.id or task.assigned_to_id == user.id

    def is_owner(self):
        return self.get_object().project.owner_id == self.request.user.id

    def get_form_class(self):
        if self.is_owner():
            return TaskOwnerUpdateForm
        return TaskStatusUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.is_owner():
            kwargs["project"] = self.get_object().project
        return kwargs

    def get_success_url(self):
        return reverse_lazy("tasks:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.assigned_to_id:
            ProjectMembership.objects.get_or_create(
                project=self.object.project,
                user=self.object.assigned_to,
                defaults={"role": ProjectMembership.Role.MEMBER},
            )
        messages.success(self.request, "Task updated.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_task"] = self.is_owner()
        return context