from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'timezone': 'UTC'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_login(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)
        
        response = self.client.post(reverse('users:login'), {
            'username': 'wrong',
            'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('users:logout'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_registration(self):
        response = self.client.get(reverse('users:registration'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('users:registration'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
            'first_name': 'New',
            'last_name': 'User',
            'timezone': 'UTC'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            timezone='UTC'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view(self):
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('users:profile'), {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'timezone': 'UTC'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')

class UserCRUDTests(TestCase):
    def setUp(self):
        # Создаем пользователя с правами администратора
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            timezone='UTC',
            is_staff=True
        )
        
        # Даем права на управление пользователями
        add_perm = Permission.objects.get(codename='add_user')
        change_perm = Permission.objects.get(codename='change_user')
        delete_perm = Permission.objects.get(codename='delete_user')
        self.admin.user_permissions.add(add_perm, change_perm, delete_perm)
        
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            timezone='UTC'
        )

