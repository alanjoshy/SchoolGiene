# Generated by Django 5.0.5 on 2024-09-14 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0008_feedback_feedback_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feedback',
            name='feedback_name',
        ),
    ]
