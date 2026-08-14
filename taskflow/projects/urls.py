from django.urls import path
from .views import ProjectCreateView, ProjectDetailView

app_name = "projects"

urlpatterns = [
    path("create/", ProjectCreateView.as_view(), name="create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="detail"),
]