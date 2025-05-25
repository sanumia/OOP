import pytest
from django.urls import reverse
from core.tests.factories import HotelFactory, TourPackageFactory, CountryFactory, UserFactory

@pytest.mark.django_db
class TestTourListView:
    def test_tour_list_view(self, client):
        TourPackageFactory.create_batch(5)
        response = client.get(reverse('core:tour_list'))
        assert response.status_code == 200
        assert len(response.context['tours']) == 5

    def test_filter_by_country(self, client):
        country = CountryFactory()
        TourPackageFactory.create_batch(3, hotel__country=country)
        TourPackageFactory.create_batch(2)
        
        response = client.get(f"{reverse('core:tour_list')}?country={country.id}")
        assert len(response.context['tours']) == 3

    def test_search_query(self, client):
        country = CountryFactory(name="Test Country")
        TourPackageFactory(hotel__country=country)
        TourPackageFactory(hotel__name="Test Hotel")
        
        response = client.get(f"{reverse('core:tour_list')}?search=Test")
        assert len(response.context['tours']) == 2

@pytest.mark.django_db
class TestTourDetailView:
    def test_tour_detail_view(self, client):
        tour = TourPackageFactory()
        response = client.get(reverse('core:tour_detail', args=[tour.pk]))
        assert response.status_code == 200
        assert response.context['tour'] == tour

    def test_related_tours(self, client):
        country = CountryFactory()
        hotel1 = HotelFactory(country=country)
        hotel2 = HotelFactory(country=country)
        main_tour = TourPackageFactory(hotel=hotel1)
        related_tour1 = TourPackageFactory(hotel=hotel2)
        related_tour2 = TourPackageFactory(hotel=hotel2)
        
        response = client.get(reverse('core:tour_detail', args=[main_tour.pk]))
        assert len(response.context['related_tours']) == 2