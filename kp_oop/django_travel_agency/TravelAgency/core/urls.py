from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.client_signup, name='client_signup'),
    path('profile/', views.profile, name='profile'),
    path('tours/', views.tour_list, name='tour_list'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]