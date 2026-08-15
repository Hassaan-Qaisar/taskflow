from django import forms
from django.contrib.auth import get_user_model

from .models import Task


User = get_user_model()


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "priority", "status", "due_date"]

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.order_by("name", "email")


class TaskOwnerUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "priority", "status", "due_date"]

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.order_by("name", "email")


class TaskStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["status"]
