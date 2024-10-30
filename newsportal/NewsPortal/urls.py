from django.urls import path, include
# Импортируем созданное нами представление
from .views import PostsList, PostDetail, PostSearch, PostCreate, NewsDelete, NewsEdit, ArticleDelete, subscribe, \
   unsubscribe, ArticleEdit, CategoryListView, OnlyNews, OnlyArt, comment, MyPosts
from django.views.decorators.cache import cache_page

urlpatterns = [
   path('i18n/', include('django.conf.urls.i18n')),
   path('', cache_page(60)(PostsList.as_view()), name='news_list'),
   path('<int:pk>', cache_page(60*5)(PostDetail.as_view()), name='news_detail'),
   path('search/', PostSearch.as_view(), name='news_search'),
   path('comment_add/<int:pk>', comment, name='comment_add'),
   path('news/', OnlyNews.as_view(), name='news'),
   path('myposts/', MyPosts.as_view(), name='myviews'),
   path('art/', OnlyArt.as_view(), name='art'),
   path('news/create/', PostCreate.as_view(), name='news_create'),
   path('news/<int:pk>/delete/', NewsDelete.as_view(), name ='news_delete'),
   path('news/<int:pk>/edit/', NewsEdit.as_view(), name='news_edit'),
   path('article/create/', PostCreate.as_view(), name='article_create'),
   path('article/<int:pk>/delete/', ArticleDelete.as_view(), name='article_delete'),
   path('article/<int:pk>/edit/', ArticleEdit.as_view(), name='article_edit'),
   path('categories/<int:pk>', CategoryListView.as_view(), name='category_list'),
   path('categories/<int:pk>/sub', subscribe, name='subscribe'),
   path('categories/<int:pk>/unsub', unsubscribe, name='unsubscribe')
]