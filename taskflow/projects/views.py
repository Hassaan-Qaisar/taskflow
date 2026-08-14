# projects/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from .forms import ProjectForm
from .models import Project, ProjectMembership


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
        # only members (owner included, since owner gets a membership row too) can view
        return self.get_object().memberships.filter(user=self.request.user).exists()