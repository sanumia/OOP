from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    ROLES = (
        ('client', 'Клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='client')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Телефон должен быть в формате: '+79999999999'."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    passport = models.CharField(max_length=100, verbose_name="Серия и номер паспорта")
    address = models.TextField(verbose_name="Адрес проживания")
    birth_date = models.DateField(verbose_name="Дата рождения", null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} (Клиент)"
class Country(models.Model):
    name = models.CharField(max_length=100)
    winter_climate = models.CharField(max_length=100)
    summer_climate = models.CharField(max_length=100)

class Hotel(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    stars = models.PositiveSmallIntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

class TourPackage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    duration_weeks = models.PositiveSmallIntegerField(choices=[(1, '1 неделя'), (2, '2 недели'), (4, '4 недели')])
    departure_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.hotel.price_per_day * self.duration_weeks * 7
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tour = models.ForeignKey(TourPackage, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)