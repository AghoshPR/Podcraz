# Generated by Django 5.1.4 on 2025-02-10 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0032_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='is_delete',
            field=models.BooleanField(default=False),
        ),
    ]
