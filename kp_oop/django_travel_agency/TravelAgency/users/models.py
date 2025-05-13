from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from datetime import date
import calendar

class User(AbstractUser):
    # Базовое поле для аватара
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    
    # Поле для номера телефона с валидацией формата 
    phone_regex = RegexValidator(
        regex=r'^\+375\s\((\d{2})\)\s\d{3}-\d{2}-\d{2}$',
        message="Номер телефона должен быть в формате: '+375 (29) XXX-XX-XX'"
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
    
    # Метод для получения текущей даты в формате DD/MM/YYYY
    def current_date_formatted(self):
        return timezone.now().strftime('%d/%m/%Y')
    
    # Метод для получения календаря в текстовом виде
    def get_text_calendar(self):
        today = timezone.now()
        cal = calendar.month(today.year, today.month)
        return cal
    
    # Метод для сохранения временных меток в локальном времени пользователя
    def save(self, *args, **kwargs):
        if not self.pk:  # Если это создание нового пользователя
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