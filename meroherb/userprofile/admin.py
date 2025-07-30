# userprofile/admin.py
from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'first_name','last_name', 'contact_number', 'location','photo']

admin.site.register(UserProfile, UserProfileAdmin)
