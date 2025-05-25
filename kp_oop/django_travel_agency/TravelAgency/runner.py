import os
import django
from django.test.utils import setup_test_environment
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'TravelAgency.settings'
django.setup()

from django.test.runner import DiscoverRunner

class TestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Дополнительная настройка тестовой среды

if __name__ == '__main__':
    test_runner = TestRunner()
    failures = test_runner.run_tests(['core.tests'])
    if failures:
        exit(1)