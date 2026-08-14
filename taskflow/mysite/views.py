from django.shortcuts import render


def home(request):
    """Render the marketing home page."""
    return render(request, "home.html")
