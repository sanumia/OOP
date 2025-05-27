# core/urls.py
from django.urls import path
from . import views
from django.urls import re_path
from .views import (
    AboutView,
    AddReviewView,
    CountryDetailView,
    CountryListView,
    CountryWeatherAPIView,
    DiscountsListView,
    HotelDetailView,
    HotelListView,
    PrivacyPolicyView,
    TourListView,
    TourDetailView,
    OrderDetailView,
    OrderCancelView,
    NewsListView,
    NewsDetailView,
    TermsView,
    FAQView,
    VacancyDetailView,
    VacancyListView,
    basket_add,
    basket_detail_view,
    basket_remove,
    basket_view,
    checkout,
    # order_detail,
    # order_list,
    order_manage,
    order_update_status,
    tour_create,
    tour_update,
    # basket_view
)

app_name = 'core'  # Пространство имен приложения

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Статистика
    path('statistics/', views.statistics_view, name='statistics'),
    
    # Страны
    path('countries/', CountryListView.as_view(), name='country_list'),
    path('countries/<int:pk>/', CountryDetailView.as_view(), name='country_detail'),
    path('api/countries/<int:country_id>/weather/', CountryWeatherAPIView.as_view(), name='country_weather'),
    
    # Отели
    path('hotels/', HotelListView.as_view(), name='hotel_list'),
    path('hotels/<int:pk>/', HotelDetailView.as_view(), name='hotel_detail'),
    
    # Туры
    path('tours/', TourListView.as_view(), name='tour_list'),
    path('tours/<int:pk>/', TourDetailView.as_view(), name='tour_detail'),
    path('tours/create/', tour_create, name='tour_create'),
    path('tours/<int:pk>/edit/', tour_update, name='tour_update'),
    
    # Корзина
    path('basket/', basket_view, name='basket_view'),
    path('baskets/', basket_detail_view, name='basket_detail'),
    path('basket/add/<int:tour_id>/', basket_add, name='basket_add'),
    path('basket/remove/<int:basket_id>/', basket_remove, name='basket_remove'),
    
    # Заказы
    path('checkout/', checkout, name='checkout'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order_cancel'),
    path('orders/manage/', order_manage, name='order_manage'),
    path('orders/<int:pk>/update/', order_update_status, name='order_update_status'),
    path('orders/<int:pk>/confirm/', views.confirm_order, name='confirm_order'),
    path('orders/<int:pk>/mark-paid/', views.mark_paid, name='mark_paid'),
    path('orders/<int:pk>/cancel-order/', views.cancel_order, name='cancel_order'),
    path('orders/export/excel/', views.export_orders_excel, name='export_orders_excel'),
    path('orders/export/pdf/', views.export_orders_pdf, name='export_orders_pdf'),
    path('orders/<int:pk>/print/', views.print_order, name='print_order'),

    # Дополнительные страницы
    path('about/', AboutView.as_view(), name='about'),
    path('add-review/', AddReviewView.as_view(), name='add_review'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('faq/', FAQView.as_view(), name='faq'),

    #Новости
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    path('discounts/', DiscountsListView.as_view(), name='discounts'),

    #ручная сериализация

    re_path(r'^export/(?P<model_name>[a-z_]+)/(?P<pk>\d+)/(?P<format_type>(json|xml|csv))/$', views.export_view, name='universal-export'),
    path('import/<str:model_name>/', views.import_view, name='universal-import'),
    path('export-data/', views.export_data, name='export_data'),
    path('import-data/', views.import_data, name='import_data'),

    # Newsletter
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    # В urlpatterns добавьте:
    path('vacancies/', VacancyListView.as_view(), name='vacancy_list'),
    path('vacancies/<slug:slug>/', VacancyDetailView.as_view(), name='vacancy_detail'),
    # path('contacts/', views.contacts, name='contacts'),
]