

from django.urls import  path

from users.views import UserCreateView, UserDeleteView, UserListView, UserUpdateView, login, profile, registration, logout

app_name = 'users'

urlpatterns = [
    path('login/', login, name='login'),  #../users/login
    path('registration/', registration, name='registration'),
    path('profile/', profile, name = 'profile' ),
    path('logout/', logout, name = 'logout' ),
    path('', UserListView.as_view(), name='user_list'),
    path('create/', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('me/update/', UserUpdateView.as_view(), name='user_update_me', kwargs={'pk': 'me'}),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('me/delete/', UserDeleteView.as_view(), name='user_delete_me', kwargs={'pk': 'me'}),

]
