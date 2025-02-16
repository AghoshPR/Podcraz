
from django.contrib import admin
from django.urls import path,include
from django.conf.urls import handler404
from . import views

handler404 = views.custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('user.urls')),
    path('myadmin/',include('myadmin.urls')),
    path('accounts/', include('allauth.urls')),
]

