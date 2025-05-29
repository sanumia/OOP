# views.py
import json
import io
import base64
from datetime import date, timedelta

from django.conf import settings
import matplotlib
matplotlib.use('Agg')  # Устанавливаем бэкенд Agg до импорта pyplot
import matplotlib.pyplot as plt
from django.views.generic import ListView, DetailView
from .models import Vacancy

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q, Min, Avg
from django.db.models.functions import TruncMonth
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, View, TemplateView, CreateView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.statistics import (
    age_statistics, 
    client_statistics, 
    popular_countries, 
    profitable_countries, 
    sales_statistics
)

from .models import (
    Country,
    Hotel,
    TourPackage,
    Order,
    Basket,
    Employee,
    News,
    PromoCode,
    Review,
    NewsletterSubscription
)
from .forms import OrderStatusForm, ReviewForm, TourPackageForm
from users.models import User
from .serializers import UniversalSerializer

from .models import Country, Hotel, TourPackage, Order, Basket
from users.models import User
import matplotlib.pyplot as plt
from django.db.models import Count, Sum, Q, Min, Avg
from django.utils import timezone 
from datetime import date, timedelta
from django.core.mail import send_mail




def home(request):
    # Get popular countries for destinations section
    popular_countries = Country.objects.annotate(
        hotels_count=Count('hotel'),
        min_price=Min('hotel__tourpackage__total_price')
    ).filter(hotels_count__gt=0)[:6]
    
    # Get popular tours for tours section
    popular_tours = TourPackage.objects.filter(
        is_active=True,
        departure_date__gte=timezone.now()
    ).select_related(
        'hotel',
        'hotel__country'
    ).order_by('departure_date')[:3]
    
    # Get testimonials for testimonials section
    testimonials = Review.objects.filter(
        is_published=True
    ).select_related('author').order_by('-created_at')[:3]

    # Get latest news
    latest_news = News.objects.filter(
        is_published=True
    ).order_by('-created_at')[:3]
    
    context = {
        'popular_countries': popular_countries,
        'popular_tours': popular_tours,
        'testimonials': testimonials,
        'latest_news': latest_news,  # Add latest news to context
        'total_clients': User.objects.filter(is_client=True).count(),
        'total_countries': Country.objects.count(),
        'total_hotels': Hotel.objects.count(),
        'years_experience': 15  # Static value for company years of experience
    }
    
    return render(request, 'core/home.html', context)

class TourListView(ListView):
    model = TourPackage
    template_name = 'core/tour_list.html'
    context_object_name = 'tours'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Поиск по стране (ID или названию)
        country_id = self.request.GET.get('country')
        search_query = self.request.GET.get('search')
        departure_date = self.request.GET.get('departure_date')
        
        if country_id:
            queryset = queryset.filter(hotel__country_id=country_id)
        
        if search_query:
            queryset = queryset.filter(
                Q(hotel__country__name__icontains=search_query) |
                Q(hotel__name__icontains=search_query)
            )
        
        if departure_date:
            queryset = queryset.filter(departure_date__gte=departure_date)
        
        # Сортировка
        sort = self.request.GET.get('sort', 'departure_date')
        if sort == 'price_asc':
            return queryset.order_by('total_price')
        elif sort == 'price_desc':
            return queryset.order_by('-total_price')
        elif sort == 'country':
            return queryset.order_by('hotel__country__name')
        elif sort == 'duration':
            return queryset.order_by('duration_weeks')
        else:  # По умолчанию сортировка по дате отправления
            return queryset.order_by('departure_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries'] = Country.objects.all().order_by('name')
        context['popular_countries'] = Country.get_popular_countries()
        
        # Сохраняем параметры поиска для пагинации
        context['current_search'] = {
            'country': self.request.GET.get('country', ''),
            'search': self.request.GET.get('search', ''),
            'departure_date': self.request.GET.get('departure_date', ''),
            'sort': self.request.GET.get('sort', 'departure_date'),
        }
        return context

class TourDetailView(DetailView):
    model = TourPackage
    template_name = 'core/tour_detail.html'
    context_object_name = 'tour'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_tours'] = TourPackage.objects.filter(
            hotel__country=self.object.hotel.country
        ).exclude(pk=self.object.pk)[:3]
        return context

@login_required
def basket_add(request, tour_id):
    tour = get_object_or_404(TourPackage, id=tour_id)
    if not tour.is_available():
        messages.error(request, 'Этот тур временно недоступен')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    basket, created = Basket.objects.get_or_create(
        user=request.user,
        tour=tour,
        defaults={'quantity': 1}
    )
    
    if not created:
        if basket.quantity < 5:  # Максимум 5 одинаковых туров
            basket.quantity += 1
            basket.save()
        else:
            messages.warning(request, 'Максимальное количество этого тура в корзине - 5')
    
    messages.success(request, 'Тур добавлен в корзину')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def basket_remove(request, basket_id):
    basket = get_object_or_404(Basket, id=basket_id, user=request.user)
    basket.delete()
    messages.success(request, 'Тур удален из корзины')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def basket_view(request):
    baskets = Basket.objects.filter(user=request.user)
    total = baskets.total_sum() if baskets else 0
    
    return render(request, 'core/baskets.html', {
        'baskets': baskets,
        'total': total
    })

@login_required
def basket_detail_view(request):
    baskets = Basket.objects.filter(user=request.user)
    total = baskets.total_sum() if baskets else 0
    
    return render(request, 'core/baskets_detail.html', {
        'baskets': baskets,
        'total': total
    })

@login_required
def checkout(request):
    baskets = Basket.objects.filter(user=request.user)
    
    if not baskets.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('core:tour_list')
    
    if request.method == 'POST':
        # Get the first basket's tour (assuming single tour checkout)
        basket = baskets.first()
        
        # Create order with calculated total price
        order = Order.objects.create(
            client=request.user,
            tour=basket.tour,
            status='pending',
            participants=basket.quantity,
            total_price=basket.tour.total_price * basket.quantity
        )
        
        # Update tour participants
        basket.tour.current_participants += basket.quantity
        basket.tour.save()
        
        # Clear basket
        baskets.delete()
        
        messages.success(request, 'Ваш заказ успешно оформлен!')
        return redirect('core:order_detail', pk=order.pk)
    
    return render(request, 'core/checkout.html', {
        'baskets': baskets,
    })

# @login_required
# def order_detail(request, pk):
#     order = get_object_or_404(Order, pk=pk, client=request.user)
#     return render(request, 'core/order_detail.html', {'order': order})

# @login_required
# def order_list(request):
#     orders = Order.objects.filter(client=request.user).order_by('-created_at')
#     return render(request, 'core/order_list.html', {'orders': orders})

#Orders
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'core/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        """Возвращает только заказы текущего пользователя"""
        return Order.objects.filter(
            client=self.request.user
        ).select_related(
            'tour', 
            'tour__hotel', 
            'tour__hotel__country',
            'manager'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context['empty_message'] = "У вас пока нет заказов"
        return context
    
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'core/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Обеспечиваем доступ только к своим заказам"""
        return Order.objects.filter(client=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['can_cancel'] = order.status == 'pending'
        context['similar_tours'] = Order.objects.filter(
            tour__hotel__country=order.tour.hotel.country
        ).exclude(id=order.id)[:3]
        return context
    
class OrderCancelView(LoginRequiredMixin, View):
    http_method_names = ['post']  # Разрешаем только POST-запросы

    def post(self, request, pk):
        order = get_object_or_404(
            Order, 
            id=pk, 
            client=request.user,
            status='pending'  # Можно отменять только ожидающие заказы
        )
        
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        
        messages.success(
            request, 
            f"Заказ #{order.id} успешно отменен"
        )
        
        return redirect('core:order_list')

# Страны
class CountryListView(ListView):
    model = Country
    template_name = 'core/country_list.html'
    context_object_name = 'countries'
    paginate_by = 12

class CountryDetailView(DetailView):
    model = Country
    template_name = 'core/country_detail.html'
    context_object_name = 'country'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        country = self.object
        
        # Обновляем данные о погоде, если они устарели (старше 1 часа) или отсутствуют
        should_update = (
            not country.weather_data or 
            not country.weather_last_updated or
            (timezone.now() - country.weather_last_updated) > timedelta(hours=1)
        )
        
        if should_update:
            country.update_weather_data()
            country.refresh_from_db()  # Обновляем объект после сохранения
        
        # Получаем популярные туры (например, 5 самых дешевых активных туров)
        popular_tours = TourPackage.objects.filter(
            hotel__country=country,
            is_active=True
        ).order_by('total_price')[:5]
        
        context.update({
            'hotels': Hotel.objects.filter(country=country),
            'tours': TourPackage.objects.filter(hotel__country=country, is_active=True),
            'popular_tours': popular_tours,
        })
        return context

# Отели
class HotelListView(ListView):
    model = Hotel
    template_name = 'core/hotel_list.html'
    context_object_name = 'hotels'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Hotel.objects.all()
        
        # Filter by country
        country_id = self.request.GET.get('country')
        if country_id:
            queryset = queryset.filter(country_id=country_id)
            
        # Filter by search query
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(country__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Filter by stars
        stars = self.request.GET.get('stars')
        if stars:
            queryset = queryset.filter(stars=stars)
            
        # Sort results
        sort = self.request.GET.get('sort', 'name')
        if sort == 'price_asc':
            queryset = queryset.annotate(min_price=Min('tourpackage__total_price')).order_by('min_price')
        elif sort == 'price_desc':
            queryset = queryset.annotate(min_price=Min('tourpackage__total_price')).order_by('-min_price')
        elif sort == 'stars':
            queryset = queryset.order_by('-stars')
        else:
            queryset = queryset.order_by('name')
            
        return queryset.select_related('country')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries'] = Country.objects.all().order_by('name')
        context['current_filters'] = {
            'country': self.request.GET.get('country', ''),
            'search': self.request.GET.get('search', ''),
            'stars': self.request.GET.get('stars', ''),
            'sort': self.request.GET.get('sort', 'name'),
        }
        return context

class HotelDetailView(DetailView):
    model = Hotel
    template_name = 'core/hotel_detail.html'
    context_object_name = 'hotel'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel = self.object
        
        # Get available tours for this hotel
        context['tours'] = TourPackage.objects.filter(
            hotel=hotel,
            is_active=True,
            departure_date__gte=timezone.now()
        ).order_by('departure_date')
        
        # Get hotel reviews
        context['reviews'] = Review.objects.filter(
            hotel=hotel,
            is_published=True
        ).select_related('author').order_by('-created_at')
        
        # Calculate average rating
        context['average_rating'] = Review.objects.filter(
            hotel=hotel,
            is_published=True
        ).aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Get similar hotels
        context['similar_hotels'] = Hotel.objects.filter(
            country=hotel.country,
            stars=hotel.stars
        ).exclude(id=hotel.id)[:3]
        
        # Add review form to context
        context['review_form'] = ReviewForm(initial={'hotel': hotel.id})
        
        return context

# Административные функции
@staff_member_required
def tour_create(request):
    if request.method == 'POST':
        form = TourPackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тур успешно создан')
            return redirect('core:tour_list')
    else:
        form = TourPackageForm()
    return render(request, 'core/tour_form.html', {'form': form})

@staff_member_required
def tour_update(request, pk):
    tour = get_object_or_404(TourPackage, pk=pk)
    if request.method == 'POST':
        form = TourPackageForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тур успешно обновлен')
            return redirect('core:tour_detail', pk=pk)
    else:
        form = TourPackageForm(instance=tour)
    return render(request, 'core/tour_form.html', {'form': form, 'tour': tour})

@staff_member_required
def order_manage(request):
    # Get all orders with related data
    orders = Order.objects.all().select_related(
        'client',
        'tour',
        'tour__hotel',
        'tour__hotel__country',
        'manager'
    ).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from and date_to:
        orders = orders.filter(created_at__range=[date_from, date_to])
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(client__email__icontains=search) |
            Q(client__first_name__icontains=search) |
            Q(client__last_name__icontains=search) |
            Q(tour__hotel__name__icontains=search)
        )
    
    # Update order status if form submitted
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        if order_id and new_status:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order_id} обновлен на {new_status}')
    
    # Pagination
    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_filters': {
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'core/order_manage.html', context)

@staff_member_required
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус заказа обновлен!')
    return redirect('core:order_manage')

@staff_member_required
def confirm_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        if order.status == 'pending':
            order.status = 'confirmed'
            order.save(update_fields=['status'])
            messages.success(request, f'Заказ #{order.id} успешно подтвержден')
        else:
            messages.error(request, 'Этот заказ нельзя подтвердить')
    return redirect('core:order_manage')

@staff_member_required
def mark_paid(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        if order.status == 'confirmed':
            order.status = 'paid'
            order.save(update_fields=['status'])
            messages.success(request, f'Заказ #{order.id} отмечен как оплаченный')
        else:
            messages.error(request, 'Этот заказ нельзя отметить как оплаченный')
    return redirect('core:order_manage')

@staff_member_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        if order.status not in ['cancelled', 'completed']:
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            messages.success(request, f'Заказ #{order.id} отменен')
        else:
            messages.error(request, 'Этот заказ нельзя отменить')
    return redirect('core:order_manage')

class AboutView(TemplateView):
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = Employee.objects.filter(is_active=True).order_by('order')
        return context



class NewsListView(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_published=True)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset.select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = News.CATEGORY_CHOICES
        return context

class NewsDetailView(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj
    
class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy_policy.html'

class AboutView(TemplateView):
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = Employee.objects.all().order_by('order')
        context['reviews'] = Review.objects.filter(is_published=True).order_by('-created_at')
        context['review_form'] = ReviewForm()
        return context

class AddReviewView(CreateView):
    model = Review
    form_class = ReviewForm
    
    def get_success_url(self):
        if self.object.hotel:
            return reverse('core:hotel_detail', kwargs={'pk': self.object.hotel.pk})
        return reverse('core:about')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Ваш отзыв успешно добавлен!')
        return super().form_valid(form)
    
class DiscountsListView(ListView):
    model = PromoCode
    template_name = 'core/discounts.html'
    context_object_name = 'promos'
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.exclude(status='expired')
            
        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_count'] = PromoCode.objects.filter(status='active').count()
        context['archived_count'] = PromoCode.objects.filter(status='archived').count()
        return context
    
#Statistics

def generate_chart(fig):
    """Конвертирует matplotlib figure в base64 для HTML"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return image_base64

@staff_member_required
def statistics_view(request):
    if not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('core:home')

    # Получаем статистические данные
    popular = TourPackage.objects.values('hotel__country__name').annotate(count=Count('id')).order_by('-count')[:5]
    profitable = TourPackage.objects.values('hotel__country__name').annotate(total=Sum('total_price')).order_by('-total')[:5]
    
    # Статистика продаж
    total_orders = Order.objects.count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Финансовая статистика - используем кэшированные значения
    from django.core.cache import cache
    total_revenue = cache.get('total_revenue')
    avg_order_value = cache.get('avg_order_value')
    
    # Если кэш пуст, вычисляем значения и сохраняем их
    if total_revenue is None:
        total_revenue = Order.objects.filter(status='paid').aggregate(total=Sum('total_price'))['total'] or 0
        cache.set('total_revenue', total_revenue)
    
    if avg_order_value is None:
        avg_order_value = Order.objects.filter(status='paid').aggregate(avg=Avg('total_price'))['avg'] or 0
        cache.set('avg_order_value', avg_order_value)
    
    # Daily sales data for the last 30 days
    today = date.today()
    last_month = today - timedelta(days=30)
    daily_sales = Order.objects.filter(
        created_at__gte=last_month,
        status='paid'
    ).values('created_at__date').annotate(
        total=Sum('total_price'),
        count=Count('id')
    ).order_by('created_at__date')

    # Prepare daily chart data
    days = []
    sales_amounts = []
    sales_counts = []
    
    for data in daily_sales:
        days.append(data['created_at__date'].strftime('%d.%m'))
        sales_amounts.append(float(data['total']))
        sales_counts.append(data['count'])
    
    # Daily sales trend chart
    if days:
        fig5, (ax5a, ax5b) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Revenue trend
        ax5a.plot(days, sales_amounts, marker='o', color='purple', linestyle='-')
        ax5a.set_title('Динамика продаж по дням (выручка)')
        ax5a.set_xlabel('Дата')
        ax5a.set_ylabel('Сумма (руб)')
        plt.setp(ax5a.xaxis.get_ticklabels(), rotation=45)
        ax5a.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on points
        for i, value in enumerate(sales_amounts):
            ax5a.annotate(f'{int(value)}', 
                         (i, value), 
                         textcoords="offset points", 
                         xytext=(0,10), 
                         ha='center')
        
        # Orders count trend
        ax5b.plot(days, sales_counts, marker='o', color='orange', linestyle='-')
        ax5b.set_title('Динамика продаж по дням (количество)')
        ax5b.set_xlabel('Дата')
        ax5b.set_ylabel('Количество заказов')
        plt.setp(ax5b.xaxis.get_ticklabels(), rotation=45)
        ax5b.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on points
        for i, value in enumerate(sales_counts):
            ax5b.annotate(str(value), 
                         (i, value), 
                         textcoords="offset points", 
                         xytext=(0,10), 
                         ha='center')
        
        plt.tight_layout()
        sales_trend_chart = generate_chart(fig5)
    else:
        sales_trend_chart = None
    

    popular_countries = [item['hotel__country__name'] for item in popular]
    popular_counts = [item['count'] for item in popular]
    
    profitable_countries = [item['hotel__country__name'] for item in profitable]
    profitable_totals = [float(item['total']) for item in profitable]
    
    # 1. График популярных стран
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(popular_countries, popular_counts, color='skyblue')
    ax1.set_title('Топ-5 популярных стран')
    ax1.set_ylabel('Количество заказов')
    plt.xticks(rotation=45)
    popular_chart = generate_chart(fig1)
    
    # 2. График прибыльных стран
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.bar(profitable_countries, profitable_totals, color='lightgreen')
    ax2.set_title('Топ-5 прибыльных стран')
    ax2.set_ylabel('Сумма (руб)')
    plt.xticks(rotation=45)
    profitable_chart = generate_chart(fig2)
    
    # 3. Распределение сумм заказов
    order_amounts = list(Order.objects.values_list('tour__total_price', flat=True))
    if order_amounts:
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        ax3.hist(order_amounts, bins=5, color='salmon', edgecolor='black')
        ax3.set_title('Распределение сумм заказов')
        ax3.set_xlabel('Сумма заказа')
        ax3.set_ylabel('Количество')
        amounts_chart = generate_chart(fig3)
    else:
        amounts_chart = None
    
    # 4. Распределение возрастов клиентов
    clients = User.objects.filter(is_client=True, birth_date__isnull=False)
    ages = []
    today = date.today()
    
    for client in clients:
        age = today.year - client.birth_date.year - (
            (today.month, today.day) < (client.birth_date.month, client.birth_date.day)
        )
        ages.append(age)
    
    if ages:
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        bins = range(18, 100, 10)
        ax4.hist(ages, bins=bins, color='gold', edgecolor='black')
        ax4.set_title('Распределение возрастов клиентов')
        ax4.set_xlabel('Возраст')
        ax4.set_ylabel('Количество клиентов')
        age_chart = generate_chart(fig4)
    else:
        age_chart = None
    
    context = {
        'popular_chart': popular_chart,
        'profitable_chart': profitable_chart,
        'amounts_chart': amounts_chart,
        'age_chart': age_chart,
        'sales_trend_chart': sales_trend_chart,
        # Sales statistics
        'total_orders': total_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
    }
    
    return render(request, 'core/statistics.html', context)

class CountryWeatherAPIView(APIView):
    def get(self, request, country_id):
        try:
            country = Country.objects.get(pk=country_id)
            weather = country.get_current_weather()
            
            if weather is None:
                return Response(
                    {'error': 'Weather data not available'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(weather, status=status.HTTP_200_OK)
            
        except Country.DoesNotExist:
            return Response(
                {'error': 'Country not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
#ручная сериализация
from .serializers import UniversalSerializer

def export_view(request, model_name, pk, format_type):
    # Получаем модель по имени
    model_map = {
        'country': Country,
        'hotel': Hotel,

    }
    
    model_class = model_map.get(model_name.lower())
    if not model_class:
        return JsonResponse({'error': 'Invalid model name'}, status=400)
    
    try:
        instance = model_class.objects.get(pk=pk)
        serialized_data = UniversalSerializer.serialize(instance, format_type)
        
        content_type = 'application/json' if format_type == 'json' else 'text/plain'
        response = HttpResponse(serialized_data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{model_name}_{pk}.{format_type}"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def import_view(request, model_name):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    model_map = {
        'country': Country,
        'hotel': Hotel,

    }
    
    model_class = model_map.get(model_name.lower())
    if not model_class:
        return JsonResponse({'error': 'Invalid model name'}, status=400)
    
    try:
        file = request.FILES['file']
        file_content = file.read().decode('utf-8')
        
        instance = UniversalSerializer.deserialize(model_class, file_content, 'json')
        return JsonResponse({
            'status': 'success',
            'model': model_name,
            'id': instance.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .serializers import UniversalSerializer
from .models import Country, Hotel, TourPackage

@staff_member_required
def export_data(request):
    if request.method == 'POST':
        model_name = request.POST.get('model')
        format_type = request.POST.get('format', 'json')
        
        model_map = {
            'country': Country,
            'hotel': Hotel,
            'tour': TourPackage,
        }
        
        model_class = model_map.get(model_name)
        if not model_class:
            return JsonResponse({'error': 'Invalid model'}, status=400)
        
        instances = model_class.objects.all()
        data = [UniversalSerializer.serialize(instance, format_type) for instance in instances]
        
        if format_type == 'json':
            content = "[" + ",\n".join(data) + "]"
            response = HttpResponse(content, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{model_name}_export.json"'
        else:
            content = "<objects>\n" + "\n".join(data) + "\n</objects>"
            response = HttpResponse(content, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{model_name}_export.xml"'
        
        return response
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        format_type = request.POST.get('format', 'json')
        
        try:
            content = file.read().decode('utf-8')
            
            if format_type == 'json':
                data = json.loads(content)
            else:
                # Обработка XML (упрощенная версия)
                data = UniversalSerializer.deserialize(content, format_type)
            
            # Здесь должна быть логика сохранения данных
            # Например, для стран:
            if isinstance(data, list):
                for item in data:
                    Country.objects.update_or_create(
                        id=item.get('id'),
                        defaults=item
                    )
            else:
                Country.objects.update_or_create(
                    id=data.get('id'),
                    defaults=data
                )
            
            return JsonResponse({'status': 'success'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

class TourFormView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = 'core/tour_form.html'
    form_class = TourPackageForm
    success_url = reverse_lazy('core:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tour_id = self.kwargs.get('tour_id')
        if tour_id:
            tour = get_object_or_404(TourPackage, id=tour_id)
            context['tour'] = tour
            context['hotel'] = tour.hotel
        return context
    
    def form_valid(self, form):
        form.instance.client = self.request.user
        form.instance.tour_id = self.kwargs.get('tour_id')
        response = super().form_valid(form)
        messages.success(self.request, 'Ваш заказ успешно создан! Мы свяжемся с вами в ближайшее время.')
        return response

class ContactView(TemplateView):
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['office_address'] = 'ул. Примерная, 123, Москва'
        context['office_phone'] = '+7 (999) 123-45-67'
        context['office_email'] = 'info@traveldream.ru'
        context['office_hours'] = 'Пн-Пт: 9:00 - 18:00'
        return context

class TermsView(TemplateView):
    template_name = 'core/terms.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['last_updated'] = '2024-05-24'  # Update this date as needed
        return context

class FAQView(TemplateView):
    template_name = 'core/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faq_categories'] = [
            {
                'name': 'Общие вопросы',
                'questions': [
                    {
                        'q': 'Как забронировать тур?',
                        'a': 'Выберите интересующий тур, добавьте его в корзину и следуйте инструкциям по оформлению заказа.'
                    },
                    {
                        'q': 'Какие способы оплаты вы принимаете?',
                        'a': 'Мы принимаем оплату банковскими картами, банковским переводом и наличными в офисе.'
                    },
                ]
            },
            {
                'name': 'Визы и документы',
                'questions': [
                    {
                        'q': 'Нужна ли виза?',
                        'a': 'Необходимость визы зависит от страны назначения. Наши менеджеры помогут вам с оформлением необходимых документов.'
                    },
                    {
                        'q': 'Какие документы нужны для поездки?',
                        'a': 'Необходим действующий загранпаспорт, виза (если требуется), медицинская страховка и ваучер на проживание.'
                    },
                ]
            },
            {
                'name': 'Отмена и изменения',
                'questions': [
                    {
                        'q': 'Можно ли отменить бронирование?',
                        'a': 'Да, но условия отмены зависят от конкретного тура и времени до начала поездки.'
                    },
                    {
                        'q': 'Как изменить даты поездки?',
                        'a': 'Свяжитесь с нашими менеджерами для обсуждения возможности изменения дат.'
                    },
                ]
            },
        ]
        return context

@login_required
def profile_view(request):
    user = request.user
    orders = Order.objects.filter(client=user).select_related(
        'tour',
        'tour__hotel',
        'tour__hotel__country'
    ).order_by('-created_at')
    
    upcoming_tours = orders.filter(
        tour__departure_date__gte=timezone.now(),
        status__in=['confirmed', 'paid']
    )
    
    past_tours = orders.filter(
        tour__departure_date__lt=timezone.now(),
        status='completed'
    )
    
    context = {
        'user': user,
        'upcoming_tours': upcoming_tours,
        'past_tours': past_tours,
        'total_spent': past_tours.aggregate(Sum('tour__total_price'))['tour__total_price__sum'] or 0,
        'favorite_country': past_tours.values('tour__hotel__country__name').annotate(
            count=Count('id')
        ).order_by('-count').first(),
    }
    
    return render(request, 'core/profile.html', context)

@login_required
def add_to_favorites(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        if hotel in request.user.favorite_hotels.all():
            request.user.favorite_hotels.remove(hotel)
            message = 'Отель удален из избранного'
        else:
            request.user.favorite_hotels.add(hotel)
            message = 'Отель добавлен в избранное'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'message': message})
        else:
            messages.success(request, message)
            return redirect('core:hotel_detail', pk=hotel_id)
    return redirect('core:hotel_detail', pk=hotel_id)

def generate_chart(fig):
    """Helper function to generate base64 chart image"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@staff_member_required
def dashboard_view(request):
    # Date range for filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Basic statistics
    total_orders = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).count()
    
    total_revenue = Order.objects.filter(
        created_at__range=[start_date, end_date],
        status='completed'
    ).aggregate(Sum('tour__total_price'))['tour__total_price__sum'] or 0
    
    # Orders by status
    orders_by_status = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('status').annotate(count=Count('id'))
    
    # Popular destinations
    popular_destinations = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).values(
        'tour__hotel__country__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Revenue by day
    revenue_by_day = Order.objects.filter(
        created_at__range=[start_date, end_date],
        status='completed'
    ).values('created_at__date').annotate(
        revenue=Sum('tour__total_price')
    ).order_by('created_at__date')
    
    # Generate charts
    # Revenue trend
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    dates = [item['created_at__date'] for item in revenue_by_day]
    revenues = [float(item['revenue']) for item in revenue_by_day]
    ax1.plot(dates, revenues)
    ax1.set_title('Динамика продаж')
    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Выручка (руб)')
    plt.xticks(rotation=45)
    revenue_chart = generate_chart(fig1)
    
    # Popular destinations pie chart
    if popular_destinations:
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        countries = [item['tour__hotel__country__name'] for item in popular_destinations]
        counts = [item['count'] for item in popular_destinations]
        ax2.pie(counts, labels=countries, autopct='%1.1f%%')
        ax2.set_title('Популярные направления')
        destinations_chart = generate_chart(fig2)
    else:
        destinations_chart = None
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_by_status': orders_by_status,
        'popular_destinations': popular_destinations,
        'revenue_chart': revenue_chart,
        'destinations_chart': destinations_chart,
        'date_range': {
            'start': start_date.date(),
            'end': end_date.date()
        }
    }
    
    return render(request, 'core/dashboard.html', context)

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                # Create or update subscription
                subscription, created = NewsletterSubscription.objects.get_or_create(
                    email=email,
                    defaults={'is_active': True}
                )
                
                if created:
                    # Send welcome email
                    try:
                        send_mail(
                            'Добро пожаловать в рассылку TravelDream!',
                            'Спасибо за подписку на нашу рассылку. Теперь вы будете получать самые интересные предложения и новости о путешествиях.',
                            settings.DEFAULT_FROM_EMAIL,
                            [email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        # Log the error but don't stop the subscription process
                        print(f"Error sending welcome email: {e}")
                    
                    messages.success(request, 'Вы успешно подписались на рассылку!')
                else:
                    if subscription.is_active:
                        messages.info(request, 'Вы уже подписаны на нашу рассылку.')
                    else:
                        subscription.is_active = True
                        subscription.save()
                        messages.success(request, 'Ваша подписка возобновлена!')
                
            except Exception as e:
                messages.error(request, 'Произошла ошибка при подписке. Пожалуйста, попробуйте позже.')
        else:
            messages.error(request, 'Пожалуйста, введите email адрес.')
    
    # Redirect back to the previous page or home
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('core:home')))

@staff_member_required
def export_orders_excel(request):
    """Export orders to Excel format"""
    import xlsxwriter
    from io import BytesIO
    
    # Create output file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Add headers
    headers = ['ID', 'Клиент', 'Тур', 'Статус', 'Дата создания', 'Сумма', 'Менеджер']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#0d6efd', 'color': 'white'})
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Get filtered orders
    orders = Order.objects.all().select_related(
        'client',
        'tour',
        'tour__hotel',
        'manager'
    )
    
    # Apply filters from request
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from and date_to:
        orders = orders.filter(created_at__range=[date_from, date_to])
    
    # Write data
    for row, order in enumerate(orders, start=1):
        worksheet.write(row, 0, order.id)
        worksheet.write(row, 1, order.client.get_full_name())
        worksheet.write(row, 2, f"{order.tour.hotel.name} ({order.tour.departure_date.strftime('%d.%m.%Y')})")
        worksheet.write(row, 3, order.get_status_display())
        worksheet.write(row, 4, order.created_at.strftime('%d.%m.%Y %H:%M'))
        worksheet.write(row, 5, float(order.total_price))
        worksheet.write(row, 6, order.manager.get_full_name() if order.manager else '-')
    
    # Set column widths
    worksheet.set_column(0, 0, 8)  # ID
    worksheet.set_column(1, 1, 25)  # Client
    worksheet.set_column(2, 2, 40)  # Tour
    worksheet.set_column(3, 3, 15)  # Status
    worksheet.set_column(4, 4, 20)  # Created At
    worksheet.set_column(5, 5, 12)  # Total Price
    worksheet.set_column(6, 6, 25)  # Manager
    
    workbook.close()
    
    # Create response
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=orders.xlsx'
    
    return response

@staff_member_required
def export_orders_pdf(request):
    """Export orders to PDF format"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from io import BytesIO
    
    # Create output file
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4))
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Get filtered orders
    orders = Order.objects.all().select_related(
        'client',
        'tour',
        'tour__hotel',
        'manager'
    )
    
    # Apply filters from request
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from and date_to:
        orders = orders.filter(created_at__range=[date_from, date_to])
    
    # Prepare data
    elements = []
    
    # Add title
    elements.append(Paragraph('Список заказов', title_style))
    elements.append(Paragraph(f'Дата формирования: {timezone.now().strftime("%d.%m.%Y %H:%M")}', normal_style))
    
    # Table data
    data = [['ID', 'Клиент', 'Тур', 'Статус', 'Дата создания', 'Сумма', 'Менеджер']]
    
    for order in orders:
        data.append([
            str(order.id),
            order.client.get_full_name(),
            f"{order.tour.hotel.name} ({order.tour.departure_date.strftime('%d.%m.%Y')})",
            order.get_status_display(),
            order.created_at.strftime('%d.%m.%Y %H:%M'),
            f"{order.total_price} руб.",
            order.manager.get_full_name() if order.manager else '-'
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Create response
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=orders.pdf'
    
    return response

@staff_member_required
def print_order(request, pk):
    """Generate a printable version of an order"""
    order = get_object_or_404(Order, pk=pk)
    
    context = {
        'order': order,
        'company_name': 'TravelDream',
        'company_address': 'ул. Примерная, 123, Москва',
        'company_phone': '+7 (999) 123-45-67',
        'company_email': 'info@traveldream.ru',
        'print_date': timezone.now(),
    }
    
    return render(request, 'core/order_print.html', context)


class VacancyListView(ListView):
    model = Vacancy
    template_name = 'core/vacancy_list.html'
    context_object_name = 'vacancies'
    
    def get_queryset(self):
        return Vacancy.objects.filter(is_published=True).order_by('-published_at')

class VacancyDetailView(DetailView):
    model = Vacancy
    template_name = 'core/vacancy_detail.html'
    context_object_name = 'vacancy'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'