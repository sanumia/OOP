from traceback import format_tb
from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from django.contrib import admin
from .models import *

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'winter_climate', 'summer_climate')

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'stars', 'price_per_day')
    list_filter = ('country', 'stars')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'tour', 'status')
    list_filter = ('status', 'tour__hotel__country')

admin.site.register(TourPackage)

class BasketAdmin(admin.TabularInline):
    model = Basket
    fields = ('tour', 'quantity', 'created_timestamp')  # Changed 'product' to 'tour'
    readonly_fields = ('created_timestamp',)

from django.contrib import admin
from .models import AgencyDetails

@admin.register(AgencyDetails)
class AgencyDetailsAdmin(admin.ModelAdmin):
    list_display = ('agency_name', 'legal_name', 'tax_id', 'phone_number', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('agency_name', 'legal_name', 'logo')
        }),
        ('Юридические реквизиты', {
            'fields': ('tax_id', 'registration_number', 'address')
        }),
        ('Контактная информация', {
            'fields': ('phone_number', 'email')
        }),
        ('Банковские реквизиты', {
            'fields': ('bank_name', 'bank_account_number', 'correspondent_account', 'bic')
        }),
        ('Руководство', {
            'fields': ('director_name',)
        }),
        ('Лицензия', {
            'fields': ('license_number', 'license_issued_by', 'license_issue_date')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
#Новости
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'display_image', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'summary', 'content', 'category')
        }),
        ('Медиа', {
            'fields': ('image', 'display_image'),
        }),
        ('Дополнительно', {
            'fields': ('author', 'is_published', 'views', 'created_at', 'updated_at'),
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return "Нет изображения"
    display_image.short_description = 'Миниатюра'

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'department', 'display_photo', 'order')
    list_filter = ('department', 'is_contact')
    search_fields = ('name', 'position', 'bio')
    list_editable = ('order',)
    
    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" />', obj.photo.url)
        return "Нет фото"
    display_photo.short_description = 'Фото'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'rating', 'created_at', 'is_published')
    list_filter = ('rating', 'is_published')
    search_fields = ('text', 'author__username')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'get_discount_display', 'start_date', 'end_date', 'status', 'is_active')
    list_filter = ('status', 'discount_type')
    search_fields = ('code', 'description')
    readonly_fields = ('current_uses', 'created_at', 'display_image')
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'description', 'image', 'display_image')
        }),
        ('Параметры скидки', {
            'fields': ('discount_type', 'discount_value', 'min_order_amount')
        }),
        ('Условия действия', {
            'fields': ('start_date', 'end_date', 'max_uses', 'current_uses')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
        ('Дополнительно', {
            'fields': ('created_at',)
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" />', obj.image.url)
        return "Нет изображения"
    display_image.short_description = 'Превью'

    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = 'Активен'