from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404
from . import views
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

handler404 = views.custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('myadmin/', include('myadmin.urls')),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in both development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
