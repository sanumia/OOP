# models.py
from django.db import models
from users.models import User
from django.core.validators import MinValueValidator

class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название страны')
    winter_climate = models.CharField(max_length=100, verbose_name='Зимний климат')
    summer_climate = models.CharField(max_length=100, verbose_name='Летний климат')
    description = models.TextField(verbose_name='Описание страны', blank=True)
    image = models.ImageField(upload_to='countries/', verbose_name='Изображение', null=True, blank=True)

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.name

class Hotel(models.Model):
    STAR_CHOICES = [
        (1, '1 звезда'),
        (2, '2 звезды'),
        (3, '3 звезды'),
        (4, '4 звезды'),
        (5, '5 звезд'),
    ]
    
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name='Страна')
    name = models.CharField(max_length=100, verbose_name='Название отеля')
    stars = models.PositiveSmallIntegerField(choices=STAR_CHOICES, verbose_name='Звездность')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за день')
    description = models.TextField(verbose_name='Описание отеля', blank=True)
    amenities = models.TextField(verbose_name='Удобства', blank=True)
    image = models.ImageField(upload_to='hotels/', verbose_name='Изображение', null=True, blank=True)
    available_rooms = models.PositiveIntegerField(default=0, verbose_name='Доступные номера')

    class Meta:
        verbose_name = 'Отель'
        verbose_name_plural = 'Отели'

    def __str__(self):
        return f"{self.name} ({self.country.name})"

class TourPackage(models.Model):
    DURATION_CHOICES = [
        (1, '1 неделя'),
        (2, '2 недели'),
        (3, '3 недели'),
        (4, '4 недели'),
    ]
    
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, verbose_name='Отель')
    duration_weeks = models.PositiveSmallIntegerField(
        choices=DURATION_CHOICES,
        verbose_name='Длительность (недели)'
    )
    departure_date = models.DateField(verbose_name='Дата отправления')
    return_date = models.DateField(verbose_name='Дата возвращения', blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая цена', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='Активный тур')
    max_participants = models.PositiveIntegerField(default=20, verbose_name='Макс. участников')
    current_participants = models.PositiveIntegerField(default=0, verbose_name='Текущие участники')

    class Meta:
        verbose_name = 'Турпакет'
        verbose_name_plural = 'Турпакеты'
        ordering = ['departure_date']

    def save(self, *args, **kwargs):
        self.total_price = self.hotel.price_per_day * self.duration_weeks * 7
        if not self.return_date:
            from datetime import timedelta
            self.return_date = self.departure_date + timedelta(weeks=self.duration_weeks)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Тур в {self.hotel.name} ({self.departure_date})"

    def is_available(self):
        return self.is_active and (self.current_participants < self.max_participants)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('paid', 'Оплачено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент', related_name='client_orders')
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Менеджер',
        related_name='managed_orders'
    )
    tour = models.ForeignKey(TourPackage, on_delete=models.PROTECT, verbose_name='Турпакет')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    notes = models.TextField(verbose_name='Примечания', blank=True)
    participants = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Количество участников'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.status == 'confirmed' and not self.manager:
            # Назначить менеджера при подтверждении заказа
            from django.contrib.auth import get_user_model
            User = get_user_model()
            manager = User.objects.filter(is_staff=True).first()
            if manager:
                self.manager = manager
        super().save(*args, **kwargs)

class BasketQuerySet(models.QuerySet):
    def total_sum(self):
        return sum(basket.sum() for basket in self)
    
    def total_quantity(self):
        return sum(basket.quantity for basket in self)


class Basket(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='Пользователь')
    tour = models.ForeignKey(to=TourPackage, on_delete=models.CASCADE, verbose_name='Тур')
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name='Количество')
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    objects = BasketQuerySet.as_manager()

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        unique_together = ('user', 'tour')

    def __str__(self):
        return f'Корзина {self.user.email} | Тур {self.tour}'
    
    def sum(self):
        return self.tour.total_price * self.quantity