from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)
    text = models.TextField(null=True)
