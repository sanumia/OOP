import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import Basket, Order

pytestmark = pytest.mark.django_db

class TestHomeView:
    def test_home_view(self, client, country, tour_package):
        url = reverse('core:home')
        response = client.get(url)
        assert response.status_code == 200
        assert 'countries' in response.context
        assert 'featured_tours' in response.context

class TestTourViews:
    def test_tour_list_view(self, client, tour_package):
        url = reverse('core:tour_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'tours' in response.context
        assert tour_package in response.context['tours']

    def test_tour_list_search(self, client, tour_package):
        url = reverse('core:tour_list')
        response = client.get(url, {'search': tour_package.hotel.name})
        assert response.status_code == 200
        assert tour_package in response.context['tours']

    def test_tour_detail_view(self, client, tour_package):
        url = reverse('core:tour_detail', kwargs={'pk': tour_package.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['tour'] == tour_package

class TestBasketViews:
    def test_basket_add(self, client, user, tour_package):
        client.force_login(user)
        url = reverse('core:basket_add', kwargs={'tour_id': tour_package.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert Basket.objects.filter(user=user, tour=tour_package).exists()

    def test_basket_remove(self, client, user, basket):
        client.force_login(user)
        url = reverse('core:basket_remove', kwargs={'basket_id': basket.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert not Basket.objects.filter(id=basket.pk).exists()

    def test_basket_view(self, client, user, basket):
        client.force_login(user)
        url = reverse('core:basket_view')
        response = client.get(url)
        assert response.status_code == 200
        assert 'baskets' in response.context
        assert basket in response.context['baskets']

class TestOrderViews:
    def test_checkout_view_empty_basket(self, client, user):
        client.force_login(user)
        url = reverse('core:checkout')
        response = client.get(url)
        assert response.status_code == 302  # Should redirect due to empty basket

    def test_checkout_view_with_items(self, client, user, basket):
        client.force_login(user)
        url = reverse('core:checkout')
        response = client.get(url)
        assert response.status_code == 200
        assert 'baskets' in response.context

    def test_checkout_process(self, client, user, basket, tour_package):
        client.force_login(user)
        url = reverse('core:checkout')
        response = client.post(url)
        assert response.status_code == 302
        
        # Check if order was created
        order = Order.objects.filter(client=user).first()
        assert order is not None
        assert order.tour == tour_package
        assert order.participants == basket.quantity
        
        # Check if basket was cleared
        assert not Basket.objects.filter(user=user).exists()

class TestCountryViews:
    def test_country_list_view(self, client, country):
        url = reverse('core:country_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'countries' in response.context
        assert country in response.context['countries']

    def test_country_detail_view(self, client, country):
        url = reverse('core:country_detail', kwargs={'pk': country.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['country'] == country

class TestHotelViews:
    def test_hotel_list_view(self, client, hotel):
        url = reverse('core:hotel_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'hotels' in response.context
        assert hotel in response.context['hotels']

    def test_hotel_detail_view(self, client, hotel):
        url = reverse('core:hotel_detail', kwargs={'pk': hotel.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['hotel'] == hotel

class TestStaffViews:
    def test_tour_create_view(self, client, staff_user):
        client.force_login(staff_user)
        url = reverse('core:tour_create')
        response = client.get(url)
        assert response.status_code == 200

    def test_tour_create_view_non_staff(self, client, user):
        client.force_login(user)
        url = reverse('core:tour_create')
        response = client.get(url)
        assert response.status_code == 302  # Should redirect to login

    def test_order_manage_view(self, client, staff_user, order):
        client.force_login(staff_user)
        url = reverse('core:order_manage')
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders' in response.context