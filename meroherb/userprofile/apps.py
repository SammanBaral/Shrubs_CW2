# userprofile/apps.py
from django.apps import AppConfig

class UserProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userprofile'

default_app_config = 'userprofile.apps.UserProfileConfig'
