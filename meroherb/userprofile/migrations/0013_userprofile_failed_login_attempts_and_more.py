# Generated by Django 5.2.4 on 2025-07-30 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0012_userprofile_email_otp_userprofile_is_email_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='failed_login_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='lockout_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
