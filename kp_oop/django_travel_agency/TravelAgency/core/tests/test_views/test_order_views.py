import pytest
from django.urls import reverse
from core.models import Order, Basket
from core.tests.factories import UserFactory, TourPackageFactory, BasketFactory

pytestmark = pytest.mark.django_db

class TestOrderViews:
    def test_order_create(self, client):
        user = UserFactory()
        client.force_login(user)
        tour = TourPackageFactory(total_price=15000)
        # Create basket first
        basket = BasketFactory(user=user, tour=tour, quantity=2)
        
        response = client.post(reverse('core:checkout'))
        assert response.status_code == 302
        assert Order.objects.count() == 1
        
        order = Order.objects.first()
        assert order.total_price == 30000  # 15000 * 2
        assert order.participants == 2
        assert order.tour == tour
        assert order.client == user