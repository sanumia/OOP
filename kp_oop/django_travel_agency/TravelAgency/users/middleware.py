# users/middleware.py
import pytz
from django.utils import timezone
from django.conf import settings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 1. Проверяем установленный часовой пояс пользователя
            if hasattr(request.user, 'timezone') and request.user.timezone:
                tz = request.user.timezone
            else:
                # 2. Пытаемся определить из заголовков браузера
                tz = request.headers.get('Timezone') or \
                     request.COOKIES.get('user_timezone') or \
                     settings.TIME_ZONE
                
                # Сохраняем для будущих посещений
                if hasattr(request.user, 'timezone'):
                    request.user.timezone = tz
                    request.user.save(update_fields=['timezone'])
            
            try:
                timezone.activate(pytz.timezone(tz))
            except pytz.UnknownTimeZoneError:
                timezone.activate(pytz.timezone(settings.TIME_ZONE))
        
        response = self.get_response(request)
        return response