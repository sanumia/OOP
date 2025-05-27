# models.py
from django.db import models
from django.urls import reverse
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
import logging
from django.db.models import Sum, Avg
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название страны')
    winter_climate = models.CharField(max_length=100, verbose_name='Зимний климат')
    summer_climate = models.CharField(max_length=100, verbose_name='Летний климат')
    description = models.TextField(verbose_name='Описание страны', blank=True)
    image = models.ImageField(upload_to='countries/', verbose_name='Изображение', null=True, blank=True)
    weather_data = models.JSONField(blank=True, null=True, verbose_name='Данные о погоде')
    weather_last_updated = models.DateTimeField(null=True, blank=True, verbose_name='Последнее обновление погоды')
    capital = models.CharField(max_length=100, verbose_name='Столица', blank=True, null=True)
    @classmethod
    def get_popular_countries(cls, limit=5):
        """Возвращает самые популярные страны по количеству туров"""
        return cls.objects.annotate(
            tour_count=models.Count('hotel__tourpackage')
        ).filter(
            tour_count__gt=0
        ).order_by('-tour_count')[:limit]
    def update_weather_data(self):
        """Обновляет данные о погоде из OpenWeather API"""
        from django.conf import settings
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not self.capital:
            logger.warning(f"Не указана столица для страны {self.name}")
            return False
            
        try:
            api_key = settings.OPENWEATHER_API_KEY
            if not api_key:
                logger.error("OPENWEATHER_API_KEY не установлен в settings.py")
                return False
                
            url = f"https://api.openweathermap.org/data/2.5/weather?q={self.capital}&appid={api_key}&units=metric&lang=ru"
            logger.info(f"Запрос погоды для {self.name} ({self.capital})")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Получены данные о погоде для {self.name}: {data}")
            
            self.weather_data = data
            self.weather_last_updated = timezone.now()
            self.save()
            
            logger.info(f"Данные о погоде для {self.name} успешно обновлены")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе погоды для {self.name} ({self.capital}): {str(e)}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении погоды для {self.name}: {str(e)}")
        return False
    def get_current_weather(self):
        """Возвращает текущую погоду в удобном формате"""
        logger = logging.getLogger(__name__)
        
        if not self.weather_data:
            logger.warning(f"Нет данных о погоде для {self.name}")
            return None
            
        try:
            weather = {
                'temp': self.weather_data['main']['temp'],
                'feels_like': self.weather_data['main']['feels_like'],
                'description': self.weather_data['weather'][0]['description'],
                'icon': self.weather_data['weather'][0]['icon'],
                'humidity': self.weather_data['main']['humidity'],
                'wind_speed': self.weather_data['wind']['speed'],
                'last_updated': self.weather_last_updated
            }
            logger.info(f"Получены форматированные данные о погоде для {self.name}: {weather}")
            return weather
        except KeyError as e:
            logger.error(f"Ошибка при форматировании данных о погоде для {self.name}: {str(e)}")
            logger.error(f"Данные о погоде: {self.weather_data}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении погоды для {self.name}: {str(e)}")
            return None

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
        # Only calculate total_price if it's not explicitly set
        if not self.pk and not self.total_price:
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
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.get_full_name()}"

    def save(self, *args, **kwargs):
        # Only calculate total_price if it's not already set
        if self.total_price is None:
            self.total_price = self.tour.total_price * self.participants
            
        # Check if status is being changed to 'paid'
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != 'paid' and self.status == 'paid':
                # Update agency statistics
                total_revenue = Order.objects.filter(status='paid').aggregate(Sum('total_price'))['total_price__sum'] or 0
                avg_order_value = Order.objects.filter(status='paid').aggregate(Avg('total_price'))['total_price__avg'] or 0
                
                # You might want to store these values in a separate Statistics model or cache them
                cache.set('total_revenue', total_revenue)
                cache.set('avg_order_value', avg_order_value)
                
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
        return f"Корзина для {self.user.username}"
    
    def sum(self):
        return self.tour.total_price * self.quantity


#Реквизиты
class AgencyDetails(models.Model):
    agency_name = models.CharField(max_length=100, verbose_name="Название агентства")
    legal_name = models.CharField(max_length=100, verbose_name="Юридическое название")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="ИНН")
    registration_number = models.CharField(max_length=50, verbose_name="ОГРН")
    address = models.CharField(max_length=200, verbose_name="Адрес")
    phone_number = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(unique=True, verbose_name="Email")
    bank_name = models.CharField(max_length=100, verbose_name="Банк")
    bank_account_number = models.CharField(max_length=50, verbose_name="Расчетный счет")
    correspondent_account = models.CharField(max_length=50, verbose_name="Корреспондентский счет")
    bic = models.CharField(max_length=20, verbose_name="БИК")
    director_name = models.CharField(max_length=100, verbose_name="Директор")
    license_number = models.CharField(max_length=50, verbose_name="Номер лицензии")
    license_issued_by = models.CharField(max_length=100, verbose_name="Кем выдана лицензия")
    license_issue_date = models.DateField(verbose_name="Дата выдачи лицензии")
    logo = models.ImageField(
        upload_to='agency/logos/',
        null=True,
        blank=True,
        verbose_name="Логотип"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Реквизиты агентства"
        verbose_name_plural = "Реквизиты агентства"
        db_table = "agency_details"

    def __str__(self):
        return self.agency_name
    
#Новости
class News(models.Model):
    CATEGORY_CHOICES = [
        ('promo', 'Акции и скидки'),
        ('country', 'Новости стран'),
        ('visa', 'Визовые новости'),
        ('airlines', 'Авиакомпании'),
        ('events', 'События'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок новости'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-адрес'
    )
    summary = models.CharField(
        max_length=250,
        verbose_name='Краткое содержание'
    )
    content = models.TextField(
        verbose_name='Полное содержание'
    )
    image = models.ImageField(
        upload_to='news/images/%Y/%m/%d/',
        verbose_name='Изображение',
        blank=True,
        null=True
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='country',
        verbose_name='Категория'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано'
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество просмотров'
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title
    

#Термины и понятия
class GlossaryTerm(models.Model):
    """Модель для словаря терминов и FAQ"""
    TERM_CATEGORIES = [
        ('general', 'Общие термины'),
        ('documents', 'Документы и визы'),
        ('transport', 'Транспорт'),
        ('accommodation', 'Проживание'),
        ('insurance', 'Страхование'),
        ('payments', 'Оплата и финансы'),
        ('safety', 'Безопасность'),
    ]

    term = models.CharField(
        max_length=200,
        verbose_name='Термин/Вопрос',
        help_text='Введите термин или вопрос'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-адрес термина',
        help_text='Уникальная часть URL для этого термина'
    )
    definition = models.TextField(
        verbose_name='Определение/Ответ',
        help_text='Полное объяснение термина или ответ на вопрос'
    )
    short_definition = models.CharField(
        max_length=250,
        verbose_name='Краткое определение',
        help_text='Краткая версия (до 250 символов)',
        blank=True
    )
    category = models.CharField(
        max_length=20,
        choices=TERM_CATEGORIES,
        default='general',
        verbose_name='Категория'
    )
    is_faq = models.BooleanField(
        default=False,
        verbose_name='Частый вопрос?',
        help_text='Отметьте, если это частый вопрос'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата добавления'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество просмотров'
    )

    class Meta:
        verbose_name = 'Термин словаря'
        verbose_name_plural = 'Термины словаря'
        ordering = ['term']
        indexes = [
            models.Index(fields=['term']),
            models.Index(fields=['category']),
            models.Index(fields=['is_faq']),
        ]

    def __str__(self):
        return self.term

    def get_absolute_url(self):
        """Генерирует URL для детальной страницы термина"""
        return reverse('glossary_term_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Автоматически создает slug при сохранении"""
        if not self.slug:
            self.slug = slugify(self.term)
            
            # Проверка уникальности slug
            original_slug = self.slug
            counter = 1
            while GlossaryTerm.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
                
        # Автоматически создаем краткое определение если не заполнено
        if not self.short_definition:
            self.short_definition = self.definition[:250] + ('...' if len(self.definition) > 250 else '')
            
        super().save(*args, **kwargs)

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views += 1
        self.save(update_fields=['views'])


class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('management', 'Руководство'),
        ('sales', 'Продажи'),
        ('booking', 'Бронирование'),
        ('marketing', 'Маркетинг'),
        ('support', 'Поддержка'),
    ]
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный сотрудник',
        help_text='Отметьте, если сотрудник работает в компании')
    name = models.CharField(max_length=100, verbose_name='ФИО')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL')
    position = models.CharField(max_length=100, verbose_name='Должность')
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default='sales',
        verbose_name='Отдел'
    )
    photo = models.ImageField(
        upload_to='employees/%Y/%m/%d/',
        verbose_name='Фото',
        blank=True,
        null=True
    )
    bio = models.TextField(verbose_name='О сотруднике')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    is_contact = models.BooleanField(
        default=True,
        verbose_name='Показывать контакты'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения'
    )
    
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.position})"
    
    def get_absolute_url(self):
        return reverse('employee_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Vacancy(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Полная занятость'),
        ('part_time', 'Частичная занятость'),
        ('remote', 'Удаленная работа'),
        ('internship', 'Стажировка'),
    ]

    DEPARTMENT_CHOICES = [
        ('sales', 'Продажи'),
        ('tour_ops', 'Туроперация'),
        ('customer_service', 'Клиентский сервис'),
        ('marketing', 'Маркетинг'),
        ('hr', 'HR'),
        ('finance', 'Финансы'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name='Название вакансии'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-адрес вакансии'
    )
    short_description = models.CharField(
        max_length=250,
        verbose_name='Краткое описание'
    )
    description = models.TextField(
        verbose_name='Полное описание'
    )
    requirements = models.TextField(
        verbose_name='Требования',
        help_text='Перечислите требования к кандидату'
    )
    responsibilities = models.TextField(
        verbose_name='Обязанности',
        help_text='Перечислите основные обязанности'
    )
    conditions = models.TextField(
        verbose_name='Условия работы',
        help_text='Что мы предлагаем'
    )
    salary = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Зарплата'
    )
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default='full_time',
        verbose_name='Тип занятости'
    )
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        verbose_name='Отдел'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )
    experience_required = models.CharField(
        max_length=100,
        verbose_name='Требуемый опыт',
        default='Без опыта'
    )

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['is_published']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_department_display()})"

    def get_absolute_url(self):
        return reverse('vacancy_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = orig_slug = slugify(self.title)
            counter = 1
            while Vacancy.objects.filter(slug=self.slug).exists():
                self.slug = f'{orig_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def is_new(self):
        return (timezone.now() - self.published_at).days <= 7
    

class Review(models.Model):
    RATING_CHOICES = [
        (5, '★★★★★'),
        (4, '★★★★☆'),
        (3, '★★★☆☆'),
        (2, '★★☆☆☆'),
        (1, '★☆☆☆☆'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Отель',
        null=True,
        blank=True
    )
    text = models.TextField(verbose_name='Текст отзыва')
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        default=5,
        verbose_name='Оценка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(  
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.author.username}"

    def get_author_name(self):
        if self.author.first_name:
            return f"{self.author.first_name} {self.author.last_name[0]}." if self.author.last_name else self.author.first_name
        return self.author.username
    


class PromoCode(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('archived', 'В архиве'),
        ('expired', 'Истекший'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Процент'),
        ('fixed', 'Фиксированная сумма'),
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Промокод'
    )
    description = models.TextField(
        verbose_name='Описание акции'
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        verbose_name='Тип скидки'
    )
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Размер скидки'
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Минимальная сумма заказа'
    )
    start_date = models.DateTimeField(
        verbose_name='Дата начала действия'
    )
    end_date = models.DateTimeField(
        verbose_name='Дата окончания действия'
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Максимальное количество использований'
    )
    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name='Текущее количество использований'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    image = models.ImageField(
        upload_to='promo_codes/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_status_display()})"

    def is_active(self):
        now = timezone.now()
        return (self.status == 'active' and 
                self.start_date <= now <= self.end_date and
                (self.max_uses is None or self.current_uses < self.max_uses))

    def save(self, *args, **kwargs):
        # Автоматическое обновление статуса
        now = timezone.now()
        if self.end_date < now:
            self.status = 'expired'
        elif self.max_uses and self.current_uses >= self.max_uses:
            self.status = 'archived'
        super().save(*args, **kwargs)

    def get_discount_display(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        return f"{self.discount_value} руб."

class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Подписка на рассылку'
        verbose_name_plural = 'Подписки на рассылку'

    def __str__(self):
        return self.email