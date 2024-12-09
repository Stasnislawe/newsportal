from django.urls import path, re_path
from . import views

urlpatterns = [
    path('dialogs/', views.DialogsView.as_view(), name='dialogs'),
    path('users/', views.Users.as_view(), name='users'),
    re_path(r'^dialogs/create/(?P<user_id>\d+)/$', views.CreateDialogView.as_view(), name='create_dialog'),
    re_path(r'^dialogs/(?P<chat_id>\d+)/$', views.MessagesView.as_view(), name='messages'),
]