from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

# Страны
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'capital', 'display_image', 'winter_climate', 'summer_climate', 'weather_status')
    list_filter = ('winter_climate', 'summer_climate')
    search_fields = ('name', 'capital', 'description')
    readonly_fields = ('weather_status_detailed', 'display_image_large')
    actions = ['update_weather_data']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'capital', 'description')
        }),
        ('Климат', {
            'fields': ('winter_climate', 'summer_climate')
        }),
        ('Изображение', {
            'fields': ('image', 'display_image_large')
        }),
        ('Погода', {
            'fields': ('weather_status_detailed', 'weather_last_updated')
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return "-"
    display_image.short_description = 'Флаг'

    def display_image_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет изображения"
    display_image_large.short_description = 'Текущее изображение'

    def weather_status(self, obj):
        if obj.weather_last_updated:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    weather_status.short_description = 'Погода'

    def weather_status_detailed(self, obj):
        if not obj.weather_data:
            return "Данные о погоде отсутствуют"
        
        weather = obj.get_current_weather()
        if not weather:
            return "Ошибка в данных о погоде"
        
        return format_html(
            """
            <div style="display: flex; align-items: center; gap: 20px;">
                <div>
                    <div style="font-size: 24px;">{temp}°C (ощущается как {feels_like}°C)</div>
                    <div>Влажность: {humidity}%</div>
                    <div>Ветер: {wind_speed} м/с</div>
                    <div>Обновлено: {last_updated}</div>
                </div>
                <div>
                    <img src="http://openweathermap.org/img/wn/{icon}@2x.png" alt="{description}">
                    <div style="text-transform: capitalize;">{description}</div>
                </div>
            </div>
            """,
            temp=weather['temp'],
            feels_like=weather['feels_like'],
            humidity=weather['humidity'],
            wind_speed=weather['wind_speed'],
            last_updated=weather['last_updated'].strftime('%Y-%m-%d %H:%M'),
            icon=weather['icon'],
            description=weather['description']
        )
    weather_status_detailed.short_description = 'Текущая погода'

    def update_weather_data(self, request, queryset):
        for country in queryset:
            success = country.update_weather_data()
            if success:
                self.message_user(request, f"Погода для {country.name} успешно обновлена")
            else:
                self.message_user(request, f"Ошибка при обновлении погоды для {country.name}", level='ERROR')
    update_weather_data.short_description = "Обновить данные о погоде"

# Отели
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_link', 'stars_display', 'price_per_day', 'available_rooms', 'display_image')
    list_filter = ('stars', 'country')
    search_fields = ('name', 'description', 'amenities')
    readonly_fields = ('display_image_large', 'country_link')
    list_editable = ('available_rooms',)
    raw_id_fields = ('country',)

    def stars_display(self, obj):
        return format_html('<span style="color: gold;">{}</span>', '★' * obj.stars)
    stars_display.short_description = 'Звёзды'

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return "-"
    display_image.short_description = 'Фото'

    def display_image_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image.url)
        return "Нет изображения"
    display_image_large.short_description = 'Текущее изображение'

    def country_link(self, obj):
        url = reverse("admin:core_country_change", args=[obj.country.id])
        return format_html('<a href="{}">{}</a>', url, obj.country.name)
    country_link.short_description = 'Страна'

# Турпакеты
@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = (
        'hotel_link', 
        'country_link',
        'duration_weeks', 
        'departure_date', 
        'return_date', 
        'total_price', 
        'availability_status',
        'participants_info'
    )
    list_filter = ('departure_date', 'hotel__country', 'duration_weeks')
    search_fields = ('hotel__name', 'hotel__country__name')
    readonly_fields = ('hotel_link', 'country_link', 'availability_status')
    date_hierarchy = 'departure_date'
    actions = ['update_return_dates']

    def hotel_link(self, obj):
        url = reverse("admin:core_hotel_change", args=[obj.hotel.id])
        return format_html('<a href="{}">{}</a>', url, obj.hotel.name)
    hotel_link.short_description = 'Отель'

    def country_link(self, obj):
        url = reverse("admin:core_country_change", args=[obj.hotel.country.id])
        return format_html('<a href="{}">{}</a>', url, obj.hotel.country.name)
    country_link.short_description = 'Страна'

    def availability_status(self, obj):
        if obj.is_available():
            return format_html('<span style="color: green; font-weight: bold;">Доступен</span>')
        return format_html('<span style="color: red;">Завершён</span>')
    availability_status.short_description = 'Статус'

    def participants_info(self, obj):
        return f"{obj.current_participants}/{obj.max_participants}"
    participants_info.short_description = 'Участники'

    def update_return_dates(self, request, queryset):
        updated = 0
        for tour in queryset.filter(return_date__isnull=True):
            tour.save()  # return_date будет обновлен в методе save()
            updated += 1
        self.message_user(request, f"Обновлено {updated} дат возвращения")
    update_return_dates.short_description = "Обновить даты возвращения"

# Заказы
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client_link',
        'tour_info',
        'status',
        'status_display',
        'total_price',
        'created_at',
        'manager_link'
    )
    list_filter = ('status', 'created_at', 'tour__hotel__country')
    search_fields = ('client__username', 'client__email', 'tour__hotel__name')
    readonly_fields = ('created_at', 'updated_at', 'client_link', 'tour_link', 'manager_link')
    list_editable = ('status',)
    raw_id_fields = ('client', 'tour', 'manager')
    date_hierarchy = 'created_at'
    actions = ['recalculate_prices']

    fieldsets = (
        ('Основная информация', {
            'fields': ('client_link', 'tour_link', 'participants', 'total_price')
        }),
        ('Статус', {
            'fields': ('status', 'manager_link', 'notes')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def client_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.get_full_name() or obj.client.username)
    client_link.short_description = 'Клиент'

    def tour_info(self, obj):
        return f"{obj.tour.hotel.name} ({obj.tour.departure_date})"
    tour_info.short_description = 'Тур'

    def tour_link(self, obj):
        url = reverse("admin:core_tourpackage_change", args=[obj.tour.id])
        return format_html('<a href="{}">{}</a>', url, self.tour_info(obj))
    tour_link.short_description = 'Тур'

    def manager_link(self, obj):
        if not obj.manager:
            return "-"
        url = reverse("admin:users_user_change", args=[obj.manager.id])
        return format_html('<a href="{}">{}</a>', url, obj.manager.get_full_name() or obj.manager.username)
    manager_link.short_description = 'Менеджер'

    def status_display(self, obj):
        colors = {
            'pending': 'gray',
            'confirmed': 'blue',
            'paid': 'green',
            'cancelled': 'red',
            'completed': 'purple',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'

    def recalculate_prices(self, request, queryset):
        updated = 0
        for order in queryset:
            order.total_price = order.tour.total_price * order.participants
            order.save()
            updated += 1
        self.message_user(request, f"Пересчитано {updated} цен")
    recalculate_prices.short_description = "Пересчитать цены"

# Корзина
class BasketAdmin(admin.TabularInline):
    model = Basket
    fields = ('tour_link', 'quantity', 'sum_display', 'created_timestamp')
    readonly_fields = ('created_timestamp', 'tour_link', 'sum_display')
    extra = 0

    def tour_link(self, obj):
        url = reverse("admin:core_tourpackage_change", args=[obj.tour.id])
        return format_html('<a href="{}">{}</a>', url, obj.tour)
    tour_link.short_description = 'Тур'

    def sum_display(self, obj):
        return f"{obj.sum()} руб."
    sum_display.short_description = 'Сумма'

# Реквизиты агентства
@admin.register(AgencyDetails)
class AgencyDetailsAdmin(admin.ModelAdmin):
    list_display = ('agency_name', 'tax_id', 'phone_number', 'email', 'display_logo')
    readonly_fields = ('created_at', 'updated_at', 'display_logo_large')

    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return "-"
    display_logo.short_description = 'Логотип'

    def display_logo_large(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" />', obj.logo.url)
        return "Логотип не загружен"
    display_logo_large.short_description = 'Текущий логотип'

# Новости
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'display_image', 'is_published', 'created_at', 'views')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'created_at', 'updated_at', 'display_image_large')
    list_editable = ('is_published',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return "-"
    display_image.short_description = 'Изображение'

    def display_image_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image.url)
        return "Изображение не загружено"
    display_image_large.short_description = 'Текущее изображение'

# Сотрудники
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'department', 'display_photo', 'is_contact', 'order')
    list_filter = ('department', 'is_contact')
    search_fields = ('name', 'position', 'bio')
    list_editable = ('order', 'is_contact')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('display_photo_large',)

    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" />', obj.photo.url)
        return "-"
    display_photo.short_description = 'Фото'

    def display_photo_large(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="200" />', obj.photo.url)
        return "Фото не загружено"
    display_photo_large.short_description = 'Текущее фото'

# Отзывы
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author_link', 'hotel_link', 'rating_display', 'created_at', 'is_published')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('text', 'author__username', 'hotel__name')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at', 'author_link', 'hotel_link')
    raw_id_fields = ('author', 'hotel')

    def author_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name() or obj.author.username)
    author_link.short_description = 'Автор'

    def hotel_link(self, obj):
        if not obj.hotel:
            return "-"
        url = reverse("admin:core_hotel_change", args=[obj.hotel.id])
        return format_html('<a href="{}">{}</a>', url, obj.hotel.name)
    hotel_link.short_description = 'Отель'

    def rating_display(self, obj):
        full_star = '★'
        empty_star = '☆'
        return format_html(
            '<span style="color: gold;">{}{}</span>',
            full_star * obj.rating,
            empty_star * (5 - obj.rating)
        )
    rating_display.short_description = 'Рейтинг'

# Промокоды
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'discount_display', 
        'start_date', 
        'end_date',
        'status',
        'status_display',
        'usage_info',
        'is_active_display'
    )
    list_filter = ('status', 'discount_type', 'start_date')
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_at', 'display_image', 'is_active_display')
    list_editable = ('status',)
    date_hierarchy = 'start_date'

    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"-{obj.discount_value}%"
        return f"-{obj.discount_value} руб."
    discount_display.short_description = 'Скидка'

    def status_display(self, obj):
        status_colors = {
            'active': 'green',
            'archived': 'gray',
            'expired': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            status_colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'

    def usage_info(self, obj):
        if obj.max_uses:
            return f"{obj.current_uses}/{obj.max_uses}"
        return f"{obj.current_uses} использований"
    usage_info.short_description = 'Использования'

    def is_active_display(self, obj):
        return obj.is_active()
    is_active_display.boolean = True
    is_active_display.short_description = 'Активен сейчас'

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Изображение отсутствует"
    display_image.short_description = 'Изображение'

# Вакансии
@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'department_display', 
        'job_type_display', 
        'salary', 
        'is_published',
        'is_new_display'
    )
    list_filter = ('department', 'job_type', 'is_published', 'published_at')
    search_fields = ('title', 'description', 'requirements')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'is_new_display')
    list_editable = ('is_published',)
    date_hierarchy = 'published_at'

    def department_display(self, obj):
        dept_colors = {
            'sales': 'blue',
            'tour_ops': 'green',
            'customer_service': 'purple',
            'marketing': 'orange',
            'hr': 'red',
            'finance': 'teal',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            dept_colors.get(obj.department, 'black'),
            obj.get_department_display()
        )
    department_display.short_description = 'Отдел'

    def job_type_display(self, obj):
        return obj.get_job_type_display()
    job_type_display.short_description = 'Тип работы'

    def is_new_display(self, obj):
        return obj.is_new()
    is_new_display.boolean = True
    is_new_display.short_description = 'Новая?'

# Термины глоссария
@admin.register(GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'category_display', 'is_faq', 'views', 'created_at')
    list_filter = ('category', 'is_faq')
    search_fields = ('term', 'definition')
    prepopulated_fields = {'slug': ('term',)}
    readonly_fields = ('views', 'created_at', 'updated_at')

    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Категория'

# Подписки на рассылку
@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at',)
    list_editable = ('is_active',)