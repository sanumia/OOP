from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date
    
from django.core.exceptions import ValidationError
import pytz

from users.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите имя пользователя'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите пароль'
    }))

    class Meta:
        model = User
        fields = ('username', 'password')


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите имя'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите фамилию'}))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите имя пользователя'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите адрес эл. почты'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': '+375 (29) XXX-XX-XX'}),
        validators=[RegexValidator(
            regex=r'^\+375(29|25|44|33)\d{7}$',
            message="Номер телефона должен быть в формате: '+375291234567'"
        )],
        required=False)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={
        'class': 'form-control py-4', 'type': 'date',
        'max': timezone.now().date() - timezone.timedelta(days=365*18)}),
        required=False)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Введите пароль'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control py-4', 'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 
                 'phone_number', 'birth_date', 'password1', 'password2')

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < 
                                                (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Пользователь должен быть старше 18 лет")
        return birth_date


class UserProfileForm(UserChangeForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4'}))
    image = forms.ImageField(widget=forms.FileInput(attrs={
        'class': 'custom-file-input'}), required=False)
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'readonly': True}))
    email = forms.CharField(widget=forms.EmailInput(attrs={
        'class': 'form-control py-4', 'readonly': True}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': '+375 (29) XXX-XX-XX'}),
        validators=[RegexValidator(
            regex=r'^\+375\s\((\d{2})\)\s\d{3}-\d{2}-\d{2}$',
            message="Номер телефона должен быть в формате: '+375 (29) XXX-XX-XX'"
        )],
        required=False)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={
        'class': 'form-control py-4', 'type': 'date',
        'max': timezone.now().date() - timezone.timedelta(days=365*18)}),
        required=False)
    is_client = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'}), required=False)
    
    # Добавляем поле для часового пояса
    timezone = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control py-4'}),
        choices=[(tz, tz) for tz in pytz.all_timezones],
        required=True,
        label="Часовой пояс"
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'image', 'username', 'email',
                 'phone_number', 'birth_date', 'is_client', 'timezone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.HiddenInput()
        
        # Автоматически определяем часовой пояс при создании формы
        if not self.instance.timezone:
            browser_tz = self.get_browser_timezone()
            if browser_tz:
                self.initial['timezone'] = browser_tz
            else:
                self.initial['timezone'] = settings.TIME_ZONE

    def get_browser_timezone(self):
        """Пытаемся получить часовой пояс из запроса"""
        request = self.request if hasattr(self, 'request') else None
        if request:
            return request.COOKIES.get('user_timezone') or \
                   request.headers.get('Timezone')
        return None

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < 
                                               (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Пользователь должен быть старше 18 лет")
        return birth_date

    def clean_timezone(self):
        """Проверяем, что часовой пояс существует"""
        timezone_str = self.cleaned_data.get('timezone')
        try:
            pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            raise forms.ValidationError("Неизвестный часовой пояс")
        return timezone_str


class AdminUserProfileForm(UserChangeForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4'}))
    image = forms.ImageField(widget=forms.FileInput(attrs={
        'class': 'custom-file-input'}), required=False)
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={
        'class': 'form-control py-4'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control py-4', 'placeholder': '+375 (29) XXX-XX-XX'}),
        validators=[RegexValidator(
            regex=r'^\+375\s\((\d{2})\)\s\d{3}-\d{2}-\d{2}$',
            message="Номер телефона должен быть в формате: '+375 (29) XXX-XX-XX'"
        )],
        required=False)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={
        'class': 'form-control py-4', 'type': 'date',
        'max': timezone.now().date() - timezone.timedelta(days=365*18)}),
        required=False)
    is_client = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'}), required=False)
    is_staff = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'}), required=False)
    is_active = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'}), required=False)
    is_superuser = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'}), required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'image', 'username', 'email',
                 'phone_number', 'birth_date', 'is_client', 'is_staff',
                 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.HiddenInput()

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < 
                                               (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Пользователь должен быть старше 18 лет")
        return birth_date


class UserForm(UserCreationForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'image', 'phone_number',
            'birth_date', 'is_client'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise ValidationError("Пользователь должен быть старше 18 лет.")
        return birth_date
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if phone_number and not phone_number.startswith('+375'):
            raise ValidationError("Номер телефона должен начинаться с +375 и соответствовать формату.")
        return phone_number

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'image',
            'phone_number', 'birth_date', 'is_client'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise ValidationError("Пользователь должен быть старше 18 лет.")
        return birth_date
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if phone_number and not phone_number.startswith('+375'):
            raise ValidationError("Номер телефона должен начинаться с +375 и соответствовать формату.")
        return phone_number