# Generated by Django 5.0 on 2024-02-02 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0009_bill_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='delivery',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
