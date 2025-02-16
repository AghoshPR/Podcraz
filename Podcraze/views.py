from django.shortcuts import render
from django.conf.urls import handler404


def custom_404(request, exception):
    return render(request, '404.html', status=404)

