from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Client

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Client

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User

class ClientSignUpForm(UserCreationForm):
    passport = forms.CharField(
        label='Серия и номер паспорта',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    address = forms.CharField(
        label='Адрес проживания',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    birth_date = forms.DateField(
        label='Дата рождения',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'first_name', 'last_name', 
                 'password1', 'password2', 'passport', 'address', 'birth_date')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.startswith('+'):
            raise ValidationError('Номер телефона должен начинаться с +')
        return phone
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'client'
        if commit:
            user.save()
            client = Client.objects.create(
                user=user,
                passport=self.cleaned_data['passport'],
                address=self.cleaned_data['address'],
                birth_date=self.cleaned_data['birth_date']
            )
        return user