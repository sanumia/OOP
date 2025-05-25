from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from datetime import date
import calendar
import pytz

from users.utils.timezone_utils import format_date_dmy, get_local_time_for_user, get_user_timezone

class User(AbstractUser):
    # Базовое поле для аватара
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    
    # Поле для номера телефона с валидацией формата 
    phone_regex = RegexValidator(
        regex=r'^\+375(29|25|44|33)\d{7}$',
        message="Номер телефона должен быть в формате: '+375291234567'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Номер телефона'
    )
    
    # Поле для даты рождения с проверкой возраста 18+
    birth_date = models.DateField(
        verbose_name='Дата рождения',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                limit_value=date(1900, 1, 1),
                message='Дата рождения не может быть раньше 1900 года'
            )
        ]
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name='Часовой пояс',
        help_text='Например: Europe/Minsk или UTC'
    )
    # Поле для определения, является ли пользователь клиентом
    is_client = models.BooleanField(default=True, verbose_name='Является клиентом')
    
    # Поля для временных меток
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания (UTC)')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления (UTC)')
    created_at_local = models.DateTimeField(verbose_name='Дата создания (локальное время)', null=True, blank=True)
    updated_at_local = models.DateTimeField(verbose_name='Дата обновления (локальное время)', null=True, blank=True)
    
    # Метод для проверки возраста 18+
    def is_adult(self):
        if not self.birth_date:
            return False
        today = date.today()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return age >= 18
    
    def get_current_date_for_user(self):
        """Текущая дата в формате DD/MM/YYYY с учетом временной зоны пользователя"""
        user_tz = get_user_timezone(self)
        now = timezone.now().astimezone(user_tz)
        return format_date_dmy(now)
    
    def get_text_calendar(self):
        """Календарь в текстовом виде для текущего месяца пользователя"""
        user_tz = get_user_timezone(self)
        now = timezone.now().astimezone(user_tz)
        return calendar.month(now.year, now.month)
    
    def get_local_created_at(self):
        """Возвращает полную дату и время создания в локальном времени"""
        if not self.date_joined:
            return "Не указано"
        local_dt = self.get_local_time(self.date_joined)
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')  # Добавлено время

    def get_local_time(self, dt):
        """Конвертирует datetime в локальное время пользователя"""
        if not dt:
            return None
        try:
            user_tz = pytz.timezone(self.timezone)
        except (pytz.UnknownTimeZoneError, AttributeError):
            user_tz = pytz.timezone(settings.TIME_ZONE)
        return timezone.localtime(dt, user_tz)
    
    def get_local_updated_at(self):
        """Дата обновления в локальном времени пользователя"""
        if not self.updated_at:
            return None
        local_dt = get_local_time_for_user(self.updated_at, self)
        return format_date_dmy(local_dt)
    
    def get_utc_created_at(self):
        """Дата создания в UTC"""
        if not self.created_at:
            return None
        return format_date_dmy(self.created_at)
    
    def get_utc_updated_at(self):
        """Дата обновления в UTC"""
        if not self.updated_at:
            return None
        return format_date_dmy(self.updated_at)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at_local = timezone.now()
        self.updated_at_local = timezone.now()
        super().save(*args, **kwargs)
 
    # Отображение в админке
    def __str__(self):
        return f"{self.username} ({self.email})" if self.email else self.username
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.CheckConstraint(
                check=models.Q(birth_date__lte=timezone.now().date() - timezone.timedelta(days=365*18)),
                name='age_18_plus'
            )
        ]