# Generated by Django 5.1.4 on 2025-02-07 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0031_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('delivered', 'Delivered'), ('payment_failed', 'Payment Failed'), ('payment_pending', 'Payment Pending')], max_length=50),
        ),
    ]
