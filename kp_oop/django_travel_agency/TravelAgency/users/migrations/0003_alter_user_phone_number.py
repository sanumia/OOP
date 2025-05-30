# Generated by Django 5.1.7 on 2025-05-13 18:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_age_18_plus_alter_user_phone_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(message="Номер телефона должен быть в формате: '+375291234567'", regex='^\\+375(29|25|44|33)\\d{7}$')], verbose_name='Номер телефона'),
        ),
    ]
