import pytest
from django.urls import reverse
from core.tests.factories import UserFactory, TourPackageFactory, OrderFactory
from django.template.loader import render_to_string

@pytest.mark.django_db
class TestStaffViews:
    def test_tour_create(self, admin_client):
        # Создаем временный шаблон для тестов
        response = admin_client.get(reverse('core:tour_create'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].__class__.__name__ == 'TourPackageForm'

    def test_tour_update(self, admin_client):
        tour = TourPackageFactory()
        response = admin_client.get(reverse('core:tour_update', args=[tour.pk]))
        assert response.status_code == 200
        assert response.context['form'].instance == tour

    def test_order_manage(self, admin_client):
        OrderFactory.create_batch(3)
        response = admin_client.get(reverse('core:order_manage'))
        assert response.status_code == 200
        assert len(response.context['orders']) == 3