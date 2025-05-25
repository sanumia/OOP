import pytest
from django.urls import reverse
from core.tests.factories import UserFactory, TourPackageFactory, BasketFactory
from core.models import Order, Basket

@pytest.mark.django_db
class TestBasketViews:
    def test_checkout(self, client):
        user = UserFactory()
        client.force_login(user)
        tour = TourPackageFactory(total_price=10000)  # Указываем total_price явно
        BasketFactory(user=user, tour=tour, quantity=2)
        
        response = client.post(reverse('core:checkout'))
        assert response.status_code == 302
        assert Order.objects.count() == 1
        order = Order.objects.first()
        assert order.total_price == 20000  # 10000 * 2
        assert Basket.objects.count() == 0