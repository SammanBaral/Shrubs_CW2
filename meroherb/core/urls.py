from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static

app_name='core'

urlpatterns=[
    path('signup/',views.signup,name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.custom_login, name="login"),
    path('verify-khalti/', views.verify_khalti, name='verify_khalti'),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_sent.html'), name="password_reset_done"), 
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_form.html'), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_done.html'), name="password_reset_complete"), 

    path('main/',views.mainpage,name="main"),


]+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)