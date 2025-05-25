from django.contrib import admin

# Register your models here.
from core.admin import BasketAdmin
from users.models import User
# Register your models here.

# admin.site.register(User)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    inlines = (BasketAdmin,)
    extra = 0