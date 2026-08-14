"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    # Include local accounts URLs before allauth so your templates take precedence
    path("accounts/", include("accounts.urls")),       # your custom register/login/logout
    path("accounts/", include("allauth.urls")),       # provides /accounts/google/login/ etc
    path("dashboard/", include("dashboard.urls")),     # dashboard view
    path("projects/", include("projects.urls")),
    path("tasks/", include("tasks.urls")),
]
