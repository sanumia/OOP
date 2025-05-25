import pytest
from django.test import Client
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import Country, Hotel, TourPackage, Order, Basket
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def admin_client(db, admin_user):
    client = Client()
    client.force_login(admin_user)
    return client

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def test_image():
    """Create a test image file"""
    file_content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return SimpleUploadedFile("test_image.gif", file_content, content_type="image/gif")

@pytest.fixture(scope='session', autouse=True)
def create_test_templates():
    # Create base templates directory
    templates_dir = os.path.join(settings.BASE_DIR, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create core templates directory
    core_templates_dir = os.path.join(settings.BASE_DIR, 'core', 'templates', 'core')
    os.makedirs(core_templates_dir, exist_ok=True)
    
    # Base template
    base_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        {% block content %}{% endblock %}
    </body>
    </html>
    """
    
    # Templates mapping
    templates = {
        os.path.join(templates_dir, 'base.html'): base_template,
        os.path.join(core_templates_dir, 'tour_form.html'): "{% extends 'base.html' %}{% block content %}{{ form }}{% endblock %}",
        os.path.join(core_templates_dir, 'order_manage.html'): "{% extends 'base.html' %}{% block content %}{% for order in orders %}{{ order }}{% endfor %}{% endblock %}",
        os.path.join(core_templates_dir, 'hotel_list.html'): "{% extends 'base.html' %}{% block content %}{% for hotel in hotels %}{{ hotel }}{% endfor %}{% endblock %}",
        os.path.join(core_templates_dir, 'hotel_detail.html'): "{% extends 'base.html' %}{% block content %}{{ hotel }}{% endblock %}",
        os.path.join(core_templates_dir, 'home.html'): "{% extends 'base.html' %}{% block content %}Home{% endblock %}",
        os.path.join(core_templates_dir, 'tour_list.html'): "{% extends 'base.html' %}{% block content %}{% for tour in tours %}{{ tour }}{% endfor %}{% endblock %}",
        os.path.join(core_templates_dir, 'tour_detail.html'): "{% extends 'base.html' %}{% block content %}{{ tour }}{% endblock %}",
        os.path.join(core_templates_dir, 'country_list.html'): "{% extends 'base.html' %}{% block content %}{% for country in countries %}{{ country }}{% endfor %}{% endblock %}",
        os.path.join(core_templates_dir, 'country_detail.html'): "{% extends 'base.html' %}{% block content %}{{ country }}{% endblock %}",
        os.path.join(core_templates_dir, 'baskets.html'): "{% extends 'base.html' %}{% block content %}{% for basket in baskets %}{{ basket }}{% endfor %}{% endblock %}",
        os.path.join(core_templates_dir, 'checkout.html'): "{% extends 'base.html' %}{% block content %}Checkout{% endblock %}"
    }
    
    # Create all templates
    for template_path, content in templates.items():
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    yield
    
    # Cleanup after tests
    for template_path in templates:
        try:
            os.remove(template_path)
        except FileNotFoundError:
            pass

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_client=True
    )

@pytest.fixture
def staff_user():
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )

@pytest.fixture
def country(test_image):
    return Country.objects.create(
        name='Test Country',
        winter_climate='Cold',
        summer_climate='Warm',
        description='Test description',
        capital='Test Capital',
        image=test_image
    )

@pytest.fixture
def hotel(country, test_image):
    return Hotel.objects.create(
        country=country,
        name='Test Hotel',
        stars=4,
        price_per_day=100.00,
        description='Test hotel description',
        amenities='WiFi, Pool',
        available_rooms=10,
        image=test_image
    )

@pytest.fixture
def tour_package(hotel):
    return TourPackage.objects.create(
        hotel=hotel,
        duration_weeks=1,
        departure_date=timezone.now().date() + timedelta(days=30),
        max_participants=20,
        current_participants=0,
        is_active=True
    )

@pytest.fixture
def order(user, tour_package):
    return Order.objects.create(
        client=user,
        tour=tour_package,
        status='pending',
        participants=2
    )

@pytest.fixture
def basket(user, tour_package):
    return Basket.objects.create(
        user=user,
        tour=tour_package,
        quantity=1
    )