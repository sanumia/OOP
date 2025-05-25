import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from core.tests.factories import CountryFactory
from django.utils import timezone
from unittest.mock import patch

pytestmark = pytest.mark.django_db

class TestCountryWeatherAPI:
    def test_country_weather_api(self, client, country):
        # Set up test weather data
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

        url = reverse('core:country_weather', kwargs={'country_id': country.id})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.json()['temp'] == 20
        assert response.json()['description'] == 'clear sky'

    def test_api_without_weather_data(self, client, country):
        url = reverse('core:country_weather', kwargs={'country_id': country.id})
        response = client.get(url)
        
        assert response.status_code == 404
        assert response.json()['error'] == 'Weather data not available'