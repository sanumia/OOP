
from django.shortcuts import render, HttpResponseRedirect
from users.forms import UserLoginForm, UserRegistrationForm, UserProfileForm
from users.models import User
from django.contrib import auth, messages
from django.urls import reverse
from core.models import Basket
from django.contrib.auth.decorators import login_required

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import UserForm, UserUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


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

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

class UserCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'auth.add_user'
    model = User
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

class UserUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'auth.change_user'
    model = User
    form_class = UserUpdateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

    def get_object(self, queryset=None):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object(queryset)

class UserDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'auth.delete_user'
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

    def get_object(self, queryset=None):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object(queryset)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object == request.user:
            return super().delete(request, *args, **kwargs)
        else:
            from django.contrib import messages
            messages.error(request, "Вы можете удалить только свой собственный аккаунт.")
            from django.shortcuts import redirect
            return redirect(self.success_url)