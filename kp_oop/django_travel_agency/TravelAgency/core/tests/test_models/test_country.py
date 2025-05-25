import pytest
from datetime import timedelta
from django.utils import timezone
from core.models import Country
from core.tests.factories import CountryFactory, TourPackageFactory
from unittest.mock import patch

@pytest.mark.django_db
class TestCountryModel:
    def test_update_weather_data(self, settings):
        settings.OPENWEATHER_API_KEY = 'test_key'
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'main': {'temp': 25},
                'weather': [{'description': 'sunny'}]
            }
            mock_get.return_value.status_code = 200
            
            country = CountryFactory(capital="TestCity")
            result = country.update_weather_data()
            
            assert result is True
            assert country.weather_data is not None
            assert 'temp' in country.weather_data['main']