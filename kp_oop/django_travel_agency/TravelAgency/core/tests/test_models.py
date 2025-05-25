import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import Country, Hotel, TourPackage, Order, Basket

pytestmark = pytest.mark.django_db

class TestCountryModel:
    def test_str_representation(self, country):
        assert str(country) == 'Test Country'

    def test_get_popular_countries(self, country, hotel, tour_package):
        popular_countries = Country.get_popular_countries(limit=1)
        assert len(popular_countries) == 1
        assert popular_countries[0] == country

    def test_weather_data_methods(self, country):
        # Test without weather data
        assert country.get_current_weather() is None

        # Test with weather data
        weather_data = {
            'main': {
                'temp': 20,
                'feels_like': 22,
                'humidity': 65
            },
            'weather': [{'description': 'clear sky', 'icon': '01d'}],
            'wind': {'speed': 5.5}
        }
        country.weather_data = weather_data
        country.weather_last_updated = timezone.now()
        country.save()

        current_weather = country.get_current_weather()
        assert current_weather['temp'] == 20
        assert current_weather['description'] == 'clear sky'

class TestHotelModel:
    def test_str_representation(self, hotel):
        assert str(hotel) == 'Test Hotel (Test Country)'

    def test_hotel_creation(self, country):
        hotel = Hotel.objects.create(
            country=country,
            name='New Hotel',
            stars=5,
            price_per_day=150.00,
            description='Luxury hotel',
            available_rooms=20
        )
        assert hotel.name == 'New Hotel'
        assert hotel.stars == 5
        assert hotel.price_per_day == Decimal('150.00')

class TestTourPackageModel:
    def test_str_representation(self, tour_package):
        expected = f"Тур в Test Hotel ({tour_package.departure_date})"
        assert str(tour_package) == expected

    def test_total_price_calculation(self, hotel):
        tour = TourPackage.objects.create(
            hotel=hotel,
            duration_weeks=2,
            departure_date=timezone.now().date() + timedelta(days=30),
            max_participants=20
        )
        # Price per day = 100.00, duration = 2 weeks (14 days)
        expected_price = Decimal('1400.00')
        assert tour.total_price == expected_price

    def test_is_available(self, tour_package):
        assert tour_package.is_available() is True
        
        # Test when tour is inactive
        tour_package.is_active = False
        tour_package.save()
        assert tour_package.is_available() is False
        
        # Test when tour is full
        tour_package.is_active = True
        tour_package.current_participants = tour_package.max_participants
        tour_package.save()
        assert tour_package.is_available() is False

class TestOrderModel:
    def test_str_representation(self, order, user):
        expected = f"Заказ #{order.id} - {user.get_full_name()}"
        assert str(order) == expected

    def test_order_status_update(self, order):
        assert order.status == 'pending'
        order.status = 'confirmed'
        order.save()
        assert order.status == 'confirmed'

class TestBasketModel:
    def test_str_representation(self, basket):
        assert str(basket) == f"Корзина для {basket.user.username}"

    def test_basket_sum(self, basket, tour_package):
        # Test single item
        assert basket.sum() == tour_package.total_price

        # Test multiple items
        basket.quantity = 2
        basket.save()
        assert basket.sum() == tour_package.total_price * 2

    def test_basket_queryset_total_sum(self, user, tour_package, hotel):
        # Create a different tour package to avoid unique constraint
        another_tour = TourPackage.objects.create(
            hotel=hotel,
            duration_weeks=2,
            departure_date=timezone.now().date() + timedelta(days=60),
            max_participants=20,
            current_participants=0,
            is_active=True
        )
        
        # Create baskets with different tours
        Basket.objects.create(user=user, tour=tour_package, quantity=1)
        Basket.objects.create(user=user, tour=another_tour, quantity=2)
        
        total = Basket.objects.filter(user=user).total_sum()
        expected_total = tour_package.total_price + (another_tour.total_price * 2)
        assert total == expected_total 