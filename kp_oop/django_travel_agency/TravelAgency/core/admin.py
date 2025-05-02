from django.contrib import admin

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