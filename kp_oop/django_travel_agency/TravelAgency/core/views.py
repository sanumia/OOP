# views.py
from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView 
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView

from .models import Country, Hotel, TourPackage, Order, Basket
from users.models import User

class CustomLoginView(LoginView):
    template_name = 'core/auth/login.html'

def home(request):
    countries = Country.objects.all()[:6]
    featured_tours = TourPackage.objects.filter(is_active=True).order_by('?')[:8]
    total_clients = User.objects.filter(is_client=True).count()
    total_countries = Country.objects.count()
    
    return render(request, 'core/home.html', {
        'countries': countries,
        'featured_tours': featured_tours,
        'total_clients': total_clients,
        'total_countries': total_countries
    })

class TourListView(ListView):
    model = TourPackage
    template_name = 'tours/tour_list.html'
    context_object_name = 'tours'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        country_id = self.request.GET.get('country')
        if country_id:
            queryset = queryset.filter(hotel__country_id=country_id)
        return queryset.order_by('departure_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries'] = Country.objects.all()
        return context

class TourDetailView(DetailView):
    model = TourPackage
    template_name = 'tours/tour_detail.html'
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
def checkout(request):
    baskets = Basket.objects.filter(user=request.user)
    if not baskets.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('tours')
    
    total = baskets.total_sum()
    
    if request.method == 'POST':
        for basket in baskets:
            if not basket.tour.is_available():
                messages.error(request, f'Тур "{basket.tour}" больше недоступен')
                return redirect('basket_view')
        
        order = Order.objects.create(
            client=request.user,
            status='pending',
            participants=sum(b.quantity for b in baskets)
        )
        
        # Добавляем туры в заказ
        for basket in baskets:
            order.tour = basket.tour
            order.save()
            basket.tour.current_participants += basket.quantity
            basket.tour.save()
        
        baskets.delete()
        messages.success(request, 'Ваш заказ успешно оформлен!')
        return redirect('order_detail', pk=order.pk)
    
    return render(request, 'orders/checkout.html', {
        'baskets': baskets,
        'total': total
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def order_list(request):
    orders = Order.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})