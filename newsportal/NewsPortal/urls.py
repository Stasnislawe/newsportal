from django.urls import path, include
# Импортируем созданное нами представление
from .views import PostsList, PostDetail, PostCreate, NewsDelete, NewsEdit, subscribe, \
   unsubscribe, CategoryListView, OnlyNews, OnlyArt, comment, MyPosts, like, dislike, deletecomment
from django.views.decorators.cache import cache_page

urlpatterns = [
   path('i18n/', include('django.conf.urls.i18n')),
   path('', cache_page(60)(PostsList.as_view()), name='news_list'),
   path('<int:pk>', cache_page(60*5)(PostDetail.as_view()), name='news_detail'),
   path('comment_add/<int:pk>', comment, name='comment_add'),
   path('comment_del/<int:pk>', deletecomment, name='comment_del'),
   path('news/', OnlyNews.as_view(), name='news'),
   path('myposts/', MyPosts.as_view(), name='myviews'),
   path('like/<int:pk>', like, name='like'),
   path('dislike/<int:pk>', dislike, name='dislike'),
   path('art/', OnlyArt.as_view(), name='art'),
   path('create/', PostCreate.as_view(), name='news_create'),
   path('<int:pk>/delete/', NewsDelete.as_view(), name ='news_delete'),
   path('<int:pk>/edit/', NewsEdit.as_view(), name='news_edit'),
   path('categories/<int:pk>', CategoryListView.as_view(), name='category_list'),
   path('categories/<int:pk>/sub', subscribe, name='subscribe'),
   path('categories/<int:pk>/unsub', unsubscribe, name='unsubscribe')
]