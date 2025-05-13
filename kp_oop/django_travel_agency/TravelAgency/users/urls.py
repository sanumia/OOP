

from django.urls import  path

from users.views import login, profile, registration, logout

app_name = 'users'

urlpatterns = [
    path('login/', login, name='login'),  #../users/login
    path('registration/', registration, name='registration'),
    path('profile/', profile, name = 'profile' ),
    path('logout/', logout, name = 'logout' ),

]
