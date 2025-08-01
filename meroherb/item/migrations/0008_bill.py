# Generated by Django 5.0.1 on 2024-02-02 06:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0007_merge_20240202_0939'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('quantity', models.CharField(max_length=255)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('bill_no', models.AutoField(primary_key=True, serialize=False)),
                ('seller', models.CharField(max_length=100, null=True)),
                ('issued_date_time', models.DateTimeField(auto_now=True)),
                ('discount_per', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('discount_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='item.item')),
            ],
        ),
    ]
