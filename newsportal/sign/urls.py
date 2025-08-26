from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import upgrade_me, IndexView, BaseRegisterView, save_author_data, delete_author_profile

urlpatterns = [
    path('login/',
         LoginView.as_view(template_name='registration/login.html'),
         name='login'),
    path('logout/',
         LogoutView.as_view(template_name='registration/logout.html'),
         name='logout'),
    path('signup/',
         BaseRegisterView.as_view(template_name='registration/signup.html'),
         name='signup'),
    path('index/', IndexView.as_view(), name='index'),
    path('index/save_author/', save_author_data, name='save_author'),
    path('index/upgrade/', upgrade_me, name='upgrade'),
    path('index/delete_author/', delete_author_profile, name='delete_author'),
]