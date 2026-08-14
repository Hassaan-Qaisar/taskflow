# dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from projects.models import Project
from tasks.models import Task


@login_required
def dashboard_view(request):
    user = request.user

    owned_projects = Project.objects.filter(owner=user).order_by("-created_at")

    assigned_tasks = (
        Task.objects.filter(assigned_to=user)
        .select_related("project")
        .order_by("-created_at")
    )

    return render(request, "dashboard/dashboard.html", {
        "owned_projects": owned_projects,
        "assigned_tasks": assigned_tasks,
    })