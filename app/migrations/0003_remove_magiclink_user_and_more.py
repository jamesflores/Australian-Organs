# Generated by Django 5.0.8 on 2025-01-05 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_logincode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='magiclink',
            name='user',
        ),
        migrations.AddIndex(
            model_name='logincode',
            index=models.Index(fields=['user', 'code'], name='app_loginco_user_id_12d9b7_idx'),
        ),
        migrations.AddIndex(
            model_name='logincode',
            index=models.Index(fields=['expires_at'], name='app_loginco_expires_79159f_idx'),
        ),
        migrations.DeleteModel(
            name='MagicLink',
        ),
    ]
