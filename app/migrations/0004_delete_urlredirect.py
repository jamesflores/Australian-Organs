# Generated by Django 5.0.8 on 2025-01-06 03:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_remove_magiclink_user_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='URLRedirect',
        ),
    ]
