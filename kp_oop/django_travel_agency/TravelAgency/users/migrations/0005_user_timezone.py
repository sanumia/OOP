# Generated by Django 5.1.7 on 2025-05-15 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_user_age_18_plus_user_age_18_plus'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='UTC', help_text='Например: Europe/Minsk или UTC', max_length=50, verbose_name='Часовой пояс'),
        ),
    ]
