from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views
from core import urls

app_name='sellerform'

urlpatterns=[
        path('seller/',views.sellerform,name='sellerform'),

] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)