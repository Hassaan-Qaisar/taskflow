# projects/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from .forms import ProjectForm
from .models import Project, ProjectMembership
from tasks.forms import TaskCreateForm


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    @transaction.atomic
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role=ProjectMembership.Role.OWNER,
        )
        return response

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def test_func(self):
        project = self.get_object()
        user = self.request.user
        if project.owner_id == user.id:
            return True
        return ProjectMembership.objects.filter(project=project, user=user).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        can_manage_project = project.owner_id == self.request.user.id

        context["tasks"] = project.tasks.select_related("assigned_to", "created_by").order_by("-created_at")
        context["can_manage_project"] = can_manage_project
        context["project_form"] = kwargs.get("project_form", ProjectForm(instance=project))
        context["task_form"] = kwargs.get("task_form", TaskCreateForm(project=project))
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.owner_id != request.user.id:
            return HttpResponseForbidden("Only the project owner can update project details or create tasks.")

        action = request.POST.get("action")
        if action == "update_project":
            project_form = ProjectForm(request.POST, instance=self.object)
            if project_form.is_valid():
                project_form.save()
                messages.success(request, "Project details updated.")
                return redirect("projects:detail", pk=self.object.pk)
            return render(
                request,
                self.template_name,
                self.get_context_data(project_form=project_form, task_form=TaskCreateForm(project=self.object)),
            )

        if action == "create_task":
            task_form = TaskCreateForm(request.POST, project=self.object)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.project = self.object
                task.created_by = request.user
                task.save()
                if task.assigned_to_id:
                    ProjectMembership.objects.get_or_create(
                        project=self.object,
                        user=task.assigned_to,
                        defaults={"role": ProjectMembership.Role.MEMBER},
                    )
                messages.success(request, "Task created.")
                return redirect("projects:detail", pk=self.object.pk)
            return render(
                request,
                self.template_name,
                self.get_context_data(project_form=ProjectForm(instance=self.object), task_form=task_form),
            )

        return redirect("projects:detail", pk=self.object.pk)