from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView, TemplateView
from .models import Post, Category, Comment, Author
from .filters import SearchFilter
from .forms import PostForm, CommentForm, AuthorForm
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required


class PostsList(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'posts.html'
    context_object_name = 'context_obj_posts'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(PostsList, self).get_context_data(**kwargs)
        pagin = Paginator(Post.objects.filter(draft=True).all().order_by('-time_create'), self.paginate_by)
        context['posts'] = pagin.page(context['page_obj'].number)
        context['top5cat'] = Category.objects.annotate(Count('subscribers')).order_by('-name_category')[:5]
        context['top3posts'] = Post.objects.annotate(Count('rating_post')).order_by('-rating_post')[:3]
        context['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        context['filterset'] = self.filterset
        return context

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
        kwargs['news'] = Post.objects.filter(post_type='NW', draft=True).all()
        kwargs['cntnews'] = Post.objects.filter(post_type='NW').count()
        kwargs['top5cat'] = Category.objects.annotate(Count('subscribers')).order_by('-name_category')[:5]
        kwargs['filterset'] = self.filterset
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs


class OnlyArt(ListView):
    model = Post
    ordering = '-time_create'
    template_name = 'art.html'
    context_object_name = 'oart'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['news'] = Post.objects.filter(post_type='AR', draft=True).all()
        kwargs['top5cat'] = Category.objects.annotate(Count('subscribers')).order_by('-name_category')[:5]
        kwargs['cntnews'] = Post.objects.filter(post_type='AR').count()
        kwargs['filterset'] = self.filterset
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs


@login_required()
def like(request, pk):
    post = Post.objects.get(pk=pk)
    post.like()
    return redirect(post.get_absolute_url())


@login_required()
def dislike(request, pk):
    post = Post.objects.get(pk=pk)
    post.dislike()
    return redirect(post.get_absolute_url())


class PostDetail(LoginRequiredMixin, DetailView):
    # Модель всё та же, но мы хотим получать информацию по отдельному товару
    model = Post
    ordering = 'heading'
    comment_form = CommentForm
    template_name = 'post.html'
    # Название объекта, в котором будет выбранный пользователем продукт
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        kwargs['comments'] = Comment.objects.filter(post_id=self.object.pk).all()
        kwargs['form'] = self.comment_form
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        return super().get_context_data(**kwargs)

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'product-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'product-{self.kwargs["pk"]}', obj)

        return obj

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()
        if self.kwargs["author"] != Author.objects.get(user=self.request.user):
            return self.handle_no_permission()
        return queryset


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


class MyPosts(PermissionRequiredMixin, ListView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    model = Post
    template_name = 'myposts.html'

    def get_context_data(self, **kwargs):
        req_user = Author.objects.get(user=self.request.user)
        kwargs['myposts'] = Post.objects.filter(author=req_user).order_by('-time_create')
        return super().get_context_data(**kwargs)


class PostCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'

    def get_context_data(self, **kwargs):
        kwargs['cats'] = Category.objects.all()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = Author.objects.get(user=self.request.user)
        # if self.object.post_type == 'AR':
        #     self.request.path == '/newsportal/article/create'
        self.object.save()
        return super().form_valid(form)


class NewsDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    model = Post
    template_name = 'myposts.html'
    success_url = reverse_lazy('myposts')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != Author.objects.get(user=self.request.user):
            return self.handle_no_permission()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class NewsEdit(PermissionRequiredMixin, UpdateView):
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    form_class = PostForm
    model = Post
    template_name = 'news_edit.html'

    def get_context_data(self, **kwargs):
        kwargs['update'] = True
        kwargs['cats'] = Category.objects.all()
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        if self.object.author != Author.objects.get(user=self.request.user):
            return self.handle_no_permission()
        return kwargs


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
def comment(request, pk):
    form = CommentForm(request.POST)
    post = get_object_or_404(Post, pk=pk)

    if form.is_valid():
        comment = Comment()
        comment.post = post
        comment.user = request.user
        comment.comment = form.cleaned_data['comment']
        photo = Author.objects.filter(user=comment.user.pk).values('photo')
        comment.save()

    return redirect(post.get_absolute_url())


@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)

    message = 'Вы успешно подписались на рассылку постов на тему'
    return render(request, 'categories/category.html', {'category': category, 'message': message})


@login_required
def unsubscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)

    message = 'Вы отписались от рассылок постов на тему'
    return render(request, 'categories/category.html', {'category': category, 'message': message})
