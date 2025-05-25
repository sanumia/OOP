from django.db.models import Sum

from core.models import Order, TourPackage
from users.models import User

def client_statistics():
    # Список клиентов в алфавитном порядке
    clients = User.objects.filter(is_client=True).order_by('last_name', 'first_name')
    
    # Общая сумма продаж
    total_sales = Order.objects.aggregate(total=Sum('tour__total_price'))['total'] or 0
    
    return {
        'clients': clients,
        'total_sales': total_sales
    }
from django.db.models import Avg
from statistics import mode, median

def sales_statistics():
    # Получаем все суммы заказов
    order_amounts = list(Order.objects.values_list('tour__total_price', flat=True))
    
    if not order_amounts:
        return None
    
    stats = {
        'average': round(sum(order_amounts) / len(order_amounts), 2),
        'median': round(median(order_amounts), 2),
    }
    
    try:
        stats['mode'] = round(mode(order_amounts), 2)
    except:
        stats['mode'] = "Нет моды (все значения уникальны)"
    
    return stats

from datetime import date
from statistics import median

def age_statistics():
    # Получаем всех клиентов с датой рождения
    clients = User.objects.filter(is_client=True, birth_date__isnull=False)
    
    # Рассчитываем возраст для каждого клиента
    today = date.today()
    ages = []
    
    for client in clients:
        age = today.year - client.birth_date.year - (
            (today.month, today.day) < (client.birth_date.month, client.birth_date.day)
        )
        ages.append(age)
    
    if not ages:
        return None
    
    return {
        'average_age': round(sum(ages) / len(ages), 1),
        'median_age': median(ages),
    }
from django.db.models import Count

def popular_countries():
    # Группируем заказы по стране и считаем количество
    popular = TourPackage.objects.values(
        'hotel__country__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return popular

from django.db.models import Sum

def profitable_countries():
    # Группируем заказы по стране и суммируем общую стоимость
    profitable = TourPackage.objects.values(
        'hotel__country__name'
    ).annotate(
        total=Sum('total_price')
    ).order_by('-total')[:5]
    
    return profitable