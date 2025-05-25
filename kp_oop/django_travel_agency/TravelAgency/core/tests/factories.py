import factory
from django.contrib.auth import get_user_model
from core.models import (
    Country, Hotel, TourPackage, Order, Basket,
    News, PromoCode, Review, Employee, AgencyDetails
)
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password')

class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country
    name = factory.Faker('country')
    capital = factory.Faker('city')
    winter_climate = "Cold"
    summer_climate = "Warm"

class HotelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hotel
    country = factory.SubFactory(CountryFactory)
    name = factory.Faker('company')
    stars = 4
    price_per_day = 5000

class TourPackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TourPackage
    hotel = factory.SubFactory(HotelFactory)
    duration_weeks = 2
    departure_date = factory.Faker('future_date')
    is_active = True
    total_price = factory.LazyAttribute(lambda obj: obj.hotel.price_per_day * obj.duration_weeks * 7)

    @factory.post_generation
    def total_price_override(self, create, extracted, **kwargs):
        if extracted:
            self.total_price = extracted
            if create:
                self.save()

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order
    client = factory.SubFactory(UserFactory)
    tour = factory.SubFactory(TourPackageFactory)
    status = 'pending'

class BasketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Basket
    user = factory.SubFactory(UserFactory)
    tour = factory.SubFactory(TourPackageFactory)

class NewsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = News
    title = factory.Faker('sentence')
    slug = factory.Sequence(lambda n: f'news-{n}')
    is_published = True

class PromoCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PromoCode
    code = factory.Sequence(lambda n: f'PROMO{n}')
    status = 'active'
    start_date = timezone.now() - timedelta(days=1)
    end_date = timezone.now() + timedelta(days=30)

class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review
    author = factory.SubFactory(UserFactory)
    is_published = True
    rating = 5

class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee
    name = factory.Faker('name')
    is_active = True

class AgencyDetailsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AgencyDetails
    agency_name = factory.Faker('company')
    email = factory.Faker('email')