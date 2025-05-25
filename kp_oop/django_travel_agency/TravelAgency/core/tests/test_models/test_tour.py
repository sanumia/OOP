import pytest
from datetime import timedelta
from django.utils import timezone
from core.models import TourPackage
from core.tests.factories import TourPackageFactory, HotelFactory

@pytest.mark.django_db
class TestTourPackageModel:
    def test_str_representation(self):
        tour = TourPackageFactory()
        assert str(tour) == f"Тур в {tour.hotel.name} ({tour.departure_date})"

    def test_save_method(self):
        hotel = HotelFactory(price_per_day=1000)
        tour = TourPackageFactory(
            hotel=hotel,
            duration_weeks=2,
            return_date=None
        )
        assert tour.total_price == 1000 * 2 * 7
        assert tour.return_date == tour.departure_date + timedelta(weeks=2)

    def test_is_available(self):
        active_tour = TourPackageFactory(is_active=True, current_participants=5, max_participants=10)
        inactive_tour = TourPackageFactory(is_active=False)
        full_tour = TourPackageFactory(is_active=True, current_participants=10, max_participants=10)
        
        assert active_tour.is_available() is True
        assert inactive_tour.is_available() is False
        assert full_tour.is_available() is False