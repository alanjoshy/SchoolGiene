# Generated by Django 5.1.1 on 2024-09-28 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paymentapp', '0005_fee_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='invoice',
            field=models.FileField(blank=True, null=True, upload_to='invoices/'),
        ),
    ]
