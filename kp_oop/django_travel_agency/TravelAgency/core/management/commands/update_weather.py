from django.core.management.base import BaseCommand
from core.models import Country
from django.utils import timezone

class Command(BaseCommand):
    help = 'Обновляет данные о погоде для всех стран'

    def handle(self, *args, **options):
        countries = Country.objects.exclude(capital__isnull=True).exclude(capital__exact='')
        
        for country in countries:
            success = country.update_weather_data()
            if success:
                self.stdout.write(f"Обновлена погода для {country.name}")
            else:
                self.stdout.write(f"Ошибка при обновлении погоды для {country.name}")
        
        self.stdout.write(self.style.SUCCESS(f"Обновление завершено. Обработано {countries.count()} стран"))