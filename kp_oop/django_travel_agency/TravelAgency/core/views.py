from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ClientSignUpForm
from .models import TourPackage, User, Client
from django.contrib.auth.views import LoginView 

class CustomLoginView(LoginView):
    template_name = 'core/auth/login.html'

def home(request):
    return render(request, 'core/home.html') 

def client_signup(request):
    """
    Обработка регистрации новых клиентов
    """
    if request.method == 'POST':
        form = ClientSignUpForm(request.POST)
        if form.is_valid():
            try:
                # Создаем пользователя
                user = form.save(commit=False)
                user.role = User.Roles.CLIENT
                user.save()
                
                # Создаем профиль клиента
                Client.objects.create(
                    user=user,
                    passport=form.cleaned_data['passport'],
                    address=form.cleaned_data['address'],
                    birth_date=form.cleaned_data['birth_date']
                )
                
                # Авторизуем пользователя
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('profile')
                
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ClientSignUpForm()
    
    return render(request, 'core/auth/signup.html', {'form': form})

@login_required
def profile(request):
    client = request.user.client
    return render(request, 'core/auth/profile.html', {'client': client})

def tour_list(request):
    tours = TourPackage.objects.all()
    return render(request, 'core/tours/list.html', {'tours': tours})