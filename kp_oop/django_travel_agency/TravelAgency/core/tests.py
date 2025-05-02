from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Client

User = get_user_model()

class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('client_signup')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+79991234567',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'passport': '1234 567890',
            'address': 'Test Address',
            'birth_date': '2000-01-01'
        }
    
    def test_signup_page_status_code(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
    
    def test_signup_template_used(self):
        response = self.client.get(self.signup_url)
        self.assertTemplateUsed(response, 'core/signup.html')
    
    def test_successful_registration(self):
        response = self.client.post(self.signup_url, data=self.valid_data)
        self.assertEqual(response.status_code, 302)  # Проверяем редирект
        
        # Проверяем создание пользователя
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, User.Roles.CLIENT)
        
        # Проверяем создание профиля клиента
        client = Client.objects.get(user=user)
        self.assertEqual(client.passport, '1234 567890')
    
    def test_invalid_phone_format(self):
        invalid_data = self.valid_data.copy()
        invalid_data['phone'] = '79991234567'  # Нет + в начале
        
        response = self.client.post(self.signup_url, data=invalid_data)
        self.assertEqual(response.status_code, 200)  # Форма не отправлена
        self.assertFormError(response, 'form', 'phone', 'Номер телефона должен начинаться с +')
    
    def test_password_mismatch(self):
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(self.signup_url, data=invalid_data)
        self.assertFormError(response, 'form', 'password2', 'Пароли не совпадают.')
    
    def test_duplicate_username(self):
        # Создаем первого пользователя
        self.client.post(self.signup_url, data=self.valid_data)
        
        # Пытаемся создать второго с тем же username
        new_data = self.valid_data.copy()
        new_data['email'] = 'new@example.com'
        response = self.client.post(self.signup_url, data=new_data)
        
        self.assertFormError(response, 'form', 'username', 'Пользователь с таким именем уже существует.')