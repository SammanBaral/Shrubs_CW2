from django.contrib.auth.forms import PasswordChangeForm
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=15, null= True, blank=True)
    location = models.CharField(max_length=50,null = True, blank=True)
    photo = models.ImageField(default='core/images/default_user.png', blank=True, null=True)
    # Add additional fields for the user profile (e.g., phone_number, etc.)

