# Generated by Django 5.0.1 on 2024-02-01 14:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_comment_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='text',
        ),
    ]
