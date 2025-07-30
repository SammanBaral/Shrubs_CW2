from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

app_name = 'userprofile'
urlpatterns =[
    path('userprofile/', views.userprofile, name='userprofile'),
]+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
