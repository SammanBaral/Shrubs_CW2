from django.urls import path, include
from django.contrib.auth.views import LogoutView

from . import views
from core import urls
from userprofile import urls

app_name='dashboard'

urlpatterns=[
    path('',include('core.urls')),
    path('dashboard/',views.dashboardView,name='dashboard'),
    path('products/',include('item.urls')),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<int:pk>',views.sellerprofile,name="sellerprofile"),
    path('home/',views.home,name="home"),
    path('', include('userprofile.urls')),
]