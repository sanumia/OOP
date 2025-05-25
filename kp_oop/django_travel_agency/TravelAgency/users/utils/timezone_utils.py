from django.utils import timezone
import pytz
from datetime import datetime
import calendar

def get_user_timezone(user):
    """Возвращает временную зону пользователя"""
    try:
        return pytz.timezone(user.timezone)
    except (pytz.UnknownTimeZoneError, AttributeError):
        return timezone.get_default_timezone()

def get_local_time_for_user(dt, user):
    """Конвертирует datetime в локальное время пользователя"""
    user_tz = get_user_timezone(user)
    if timezone.is_aware(dt):
        return timezone.localtime(dt, user_tz)
    return user_tz.localize(dt)

def format_date_dmy(dt):
    """Форматирует дату в DD/MM/YYYY"""
    return dt.strftime('%d/%m/%Y')