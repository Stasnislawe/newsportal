from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView, TemplateView
from .models import Post, Category
from .filters import SearchFilter
from .forms import PostForm
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .tasks import new_post_added

class PostsList(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['top5cat'] = Category.objects.annotate(Count('subscribers')).order_by('-name_category')[:5]
        kwargs['top3posts'] = Post.objects.annotate(Count('rating_post')).order_by('-rating_post')[:3]
        kwargs['filterset'] = self.filterset
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs


class OnlyNews(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'news.html'
    context_object_name = 'onews'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['news'] = Post.objects.filter(post_type='NW').all()
        return super().get_context_data(**kwargs)


class OnlyArt(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'art.html'
    context_object_name = 'oart'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['news'] = Post.objects.filter(post_type='AR')
        kwargs['cntnews'] = Post.objects.filter(post_type='AR').count()
        return super().get_context_data(**kwargs)


class PostDetail(DetailView):
    # Модель всё та же, но мы хотим получать информацию по отдельному товару
    model = Post
    ordering = 'heading'
    template_name = 'post.html'
    # Название объекта, в котором будет выбранный пользователем продукт
    context_object_name = 'post'

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'product-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'product-{self.kwargs["pk"]}', obj)

        return obj


class PostSearch(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'posts_search.html'
    context_object_name = 'post_search'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs

class PostCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        if self.request.path == '/newsportal/article/create/':
            post.post_type = 'AR'
        post.save()
        #new_post_added.delay(post.pk)
        return super().form_valid(form)

class NewsDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    model = Post
    template_name = 'news_delete.html'
    success_url = reverse_lazy('news_list')

class NewsEdit(PermissionRequiredMixin, UpdateView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    form_class = PostForm
    model = Post
    template_name = 'news_edit.html'

class ArticleDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    model = Post
    template_name = 'article_delete.html'
    success_url = reverse_lazy('news_list')

class ArticleEdit(PermissionRequiredMixin, UpdateView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    form_class = PostForm
    model = Post
    template_name = 'article_edit.html'

class CategoryListView(PostsList):
    model = Post
    template_name = 'categories/category.html'
    context_object_name = 'category_news_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(posts_mtm=self.category).order_by('-time_create')
        self.filterset = SearchFilter(self.request.GET, queryset)
        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['if_subscriber'] = self.request.user in self.category.subscribers.all()
        context['category'] = self.category
        context['filterset'] = self.filterset
        return context

@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)

    message = 'Вы успешно подписались на рассылку постов на тему'
    return render(request, 'categories/subc.html', {'category': category, 'message': message})

@login_required
def unsubscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)

    message = 'Вы отписались от рассылок постов на тему'
    return render(request, 'categories/subc.html', {'category': category, 'message': message})

