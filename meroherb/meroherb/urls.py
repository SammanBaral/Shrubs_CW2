# main/urls.py

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from core.views import mainpage
from django.urls import path, include

# Import Debug Toolbar only for development


app_name = "meroherb"

urlpatterns = [
    path('', include('core.urls')),
    path('',mainpage,name="first"),
    path('', include('dashboard.urls')),
    path('password_reset/', include('django.contrib.auth.urls')),
    path('', include('item.urls')),
    path('', include('sellerform.urls')),
    path('', include('userprofile.urls')),
    path('inbox/', include('chatting.urls')),
    path('admin/', admin.site.urls),
]

# Add Debug Toolbar URL patterns only for developments

# Serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
