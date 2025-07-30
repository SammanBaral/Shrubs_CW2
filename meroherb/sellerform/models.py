from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class SellerAccount(models.Model):
    user=models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    image=models.ImageField(null=True, blank=True)


    def __str__(self):
        return self.user.username
    