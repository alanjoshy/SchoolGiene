# Generated by Django 5.0.5 on 2024-09-24 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paymentapp', '0004_fee_created_at_fee_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='fee',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
