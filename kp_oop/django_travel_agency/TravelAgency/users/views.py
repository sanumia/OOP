
from django.shortcuts import render, HttpResponseRedirect
from users.forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from users.models import User
from django.contrib import auth, messages
from django.urls import reverse
from core.models import Basket
from django.contrib.auth.decorators import login_required

# Create your views here.
def login(request):

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST) #получаем данные из формы
        if form.is_valid():  #проверяем, валидны ли данные
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password =password) # существует ли уже такой user(подтвержденеи подлинности)
            if user:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('home'))
    else:
        form = UserLoginForm()
    context = {'form':form}
    return render(request, 'users/login.html', context)

def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(data = request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Поздравляем! Вы успешно зарегестрировались.')
            return HttpResponseRedirect(reverse('users:login'))
    else:
        form = UserRegistrationForm()
    context = {'form':form}
    return render(request, 'users/registration.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(instance=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users:profile')) #redirect чтобы после обновления пользователь остался на этой же странице
        else:
            print(form.errors)
    else:
        form = UserProfileForm(instance=request.user) #в форму передаются данные пользователя
    baskets = Basket.objects.filter(user=request.user)

    context = {'title':'Store - Каталог',
                'form':form,
                'baskets': Basket.objects.filter(user=request.user),

            }
    return render(request, 'users/profile.html', context)

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('home'))