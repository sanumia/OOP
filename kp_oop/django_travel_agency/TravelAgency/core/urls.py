# core/urls.py
from django.urls import path
from . import views
from .views import (
    TourListView,
    TourDetailView,
    basket_add,
    basket_remove,
    checkout,
    order_detail,
    order_list,
    # basket_view
)

app_name = 'core'  # Пространство имен приложения

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Туры
    path('tours/', TourListView.as_view(), name='tour_list'),
    path('tours/<int:pk>/', TourDetailView.as_view(), name='tour_detail'),
    
    # Корзина
    # path('basket/', basket_view, name='basket_view'),
    path('basket/add/<int:tour_id>/', basket_add, name='basket_add'),
    path('basket/remove/<int:basket_id>/', basket_remove, name='basket_remove'),
    
    # Заказы
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_list, name='order_list'),
    path('orders/<int:pk>/', order_detail, name='order_detail'),
    
    # Дополнительные страницы
    # path('about/', views.about, name='about'),
    # path('contacts/', views.contacts, name='contacts'),
]