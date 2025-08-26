from asgiref.sync import sync_to_async, async_to_sync
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView, TemplateView
from .models import Post, Category, Comment, Author, Likes, Dislikes, CommentRating
from .filters import SearchFilter
from .forms import PostForm, CommentForm, AuthorForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from .tasks import new_post_added


class PostsList(ListView):
    """Вьюха просмотра всех постов"""
    model = Post
    ordering = '-time_create'
    template_name = 'post/posts.html'
    queryset = Post.objects.filter(draft=True).all().order_by('-time_create')
    context_object_name = 'posts'
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super(PostsList, self).get_context_data(**kwargs)
        # pagin = Paginator(Post.objects.filter(draft=True).all().order_by('-time_create'), self.paginate_by)
        # context['posts'] = pagin.page(context['page_obj'].number)
        context['top5cat'] = Category.objects.filter(postcategory__post__draft=True).annotate(total=Count('subscribers')).order_by('-total')[:5]
        context['top3posts'] = Post.objects.filter(postcategory__post__draft=True).annotate(Count('post_likes__rate')).order_by('-post_likes__rate')[:3]
        context['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        context['filterset'] = self.filterset
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs


class CustomSuccessMessageMixin:
    """Вызов сообщений на экран"""
    @property
    def success_msg(self):
        return False

    def form_valid(self, form):
        messages.success(self.request, self.success_msg)
        return super().form_valid(form)

    def get_success_url(self):
        return '%s?id=%s' % (self.success_url, self.object.id)


class OnlyNews(ListView):
    """Вью просмотра всех новостей"""
    model = Post
    ordering = '-time_create'
    template_name = 'news.html'
    context_object_name = 'onews'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['news'] = Post.objects.filter(post_type='NW', draft=True).all()
        kwargs['cntnews'] = Post.objects.filter(post_type='NW').count()
        kwargs['top5cat'] = Category.objects.filter(postcategory__post__draft=True).annotate(
            total=Count('subscribers')).order_by('-total')[:5]
        kwargs['top3posts'] = Post.objects.filter(postcategory__post__draft=True).annotate(
            Count('post_likes__rate')).order_by('-post_likes__rate')[:3]
        kwargs['filterset'] = self.filterset
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return self.filterset.qs


class OnlyArt(ListView):
    """Вью просмотра всех статей"""
    model = Post
    ordering = '-time_create'
    template_name = 'art.html'
    context_object_name = 'oart'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['news'] = Post.objects.filter(post_type='AR', draft=True).all()
        kwargs['top5cat'] = Category.objects.filter(postcategory__post__draft=True).annotate(
            total=Count('subscribers')).order_by('-total')[:5]
        kwargs['top3posts'] = Post.objects.filter(postcategory__post__draft=True).annotate(
            Count('post_likes__rate')).order_by('-post_likes__rate')[:3]
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
    """Функция лайка"""
    user = request.user
    post = Post.objects.get(pk=pk)
    if not Likes.objects.filter(rating=post).exists():
        rate = Likes(rating=post)
        rate.save()
        rate.user.add(user)
        rate.save()
        rate.like()
    elif user.pk in Post.objects.filter(postcategory__post__draft=True, pk=pk).values_list('post_likes__user', flat=True):
        rate = Likes.objects.get(rating=post)
        rate.dislike()
        rate.user.remove(user)
        rate.save()
    elif user.pk not in Post.objects.filter(postcategory__post__draft=True, pk=pk).values_list('post_likes__user', flat=True):
        rate = Likes.objects.get(rating=post)
        rate.user.add(user)
        rate.save()
        rate.like()
    return redirect(post.get_absolute_url())


@login_required()
def dislike(request, pk):
    """"Функция дизлайка"""
    user = request.user
    post = Post.objects.get(pk=pk)
    if not Dislikes.objects.filter(rating=post).exists():
        rate = Dislikes(rating=post)
        rate.save()
        rate.user.add(user)
        rate.save()
        rate.like()
    elif user.pk in Post.objects.filter(postcategory__post__draft=True, pk=pk).values_list('post_dislikes__user', flat=True):
        rate = Dislikes.objects.get(rating=post)
        rate.dislike()
        rate.user.remove(user)
        rate.save()
    elif user.pk not in Post.objects.filter(postcategory__post__draft=True, pk=pk).values_list('post_dislikes__user', flat=True):
        rate = Dislikes.objects.get(rating=post)
        rate.like()
        rate.user.add(user)
        rate.save()
    return redirect(post.get_absolute_url())


class PostDetail(LoginRequiredMixin, DetailView):
    """Вью просмотра поста"""
    # Модель всё та же, но мы хотим получать информацию по отдельному товару
    model = Post
    ordering = 'heading'
    comment_form = CommentForm
    template_name = 'post/post.html'
    # Название объекта, в котором будет выбранный пользователем продукт
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        kwargs['comments'] = Comment.objects.filter(post_id=self.object.pk).all()
        kwargs['form'] = self.comment_form
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        likes = Likes.objects.filter(rating=self.object.pk).aggregate(sm=Coalesce(Sum('rate'), 0)).get('sm')
        dislikes = Dislikes.objects.filter(rating=self.object.pk).aggregate(sm=Coalesce(Sum('rate'), 0)).get('sm')
        kwargs['likes'] = likes
        kwargs['dislikes'] = dislikes
        return super().get_context_data(**kwargs)

    def get_object(self, *args, **kwargs):
        current_post = Post.objects.get(id=self.kwargs["pk"])
        # obj = cache.get(f'product-{self.kwargs["pk"]}', None)
        # if not obj:
        #     obj = super().get_object(queryset=self.queryset)
        #     cache.set(f'product-{self.kwargs["pk"]}', obj)
        if (current_post.draft==False) and (current_post.author.user != self.request.user):
            return self.handle_no_permission()

        return current_post


class MyPosts(PermissionRequiredMixin, ListView):
    """Вью просмотра моих постов"""
    permission_required = ('NewsPortal.add_post', 'NewsPortal.change_post', 'NewsPortal.delete_post')
    model = Post
    template_name = 'post/myposts.html'

    def get_context_data(self, **kwargs):
        req_user = Author.objects.get(user=self.request.user)
        kwargs['myposts'] = Post.objects.filter(author=req_user).order_by('-time_create')
        return super().get_context_data(**kwargs)


class PostCreate(PermissionRequiredMixin, CreateView):
    """Вью создания поста"""
    permission_required = 'NewsPortal.add_post'
    form_class = PostForm
    model = Post
    template_name = 'post/post_create.html'

    def get_form_kwargs(self):
        user = self.request.user
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': user})
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['cats'] = Category.objects.all()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = Author.objects.get(user=self.request.user)
        self.object.save()
        new_post_added.delay(self.object.pk)
        return super().form_valid(form)


class NewsDelete(PermissionRequiredMixin, DeleteView):
    """Вью удаления поста"""
    permission_required = 'NewsPortal.delete_post'
    model = Post
    template_name = 'post/myposts.html'
    success_url = reverse_lazy('myposts')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != Author.objects.get(user=self.request.user):
            return self.handle_no_permission()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class NewsEdit(PermissionRequiredMixin, UpdateView):
    """Вью редактирования поста"""
    permission_required = 'NewsPortal.change_post'
    form_class = PostForm
    model = Post
    template_name = 'post/news_edit.html'

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
    """Вью просмотра постов по категориям"""
    model = Post
    template_name = 'categories/category.html'
    context_object_name = 'category_news_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(posts_mtm=self.category, draft=True).order_by('-time_create').distinct()
        self.filterset = SearchFilter(self.request.GET, queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top5cat'] = Category.objects.filter(postcategory__post__draft=True).annotate(Count('subscribers')).order_by('-name_category')[:5]
        context['is_not_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['if_subscriber'] = self.request.user in self.category.subscribers.all()
        context['category'] = self.category
        context['filterset'] = self.filterset
        return context


@login_required
def comment(request, pk):
    """"Функция коммента"""
    form = CommentForm(request.POST)
    post = get_object_or_404(Post, pk=pk)

    if form.is_valid():
        comment = Comment()
        comment.post = post
        comment.user = request.user
        comment.comment = form.cleaned_data['comment']
        comment.save()

    return redirect(post.get_absolute_url())


@login_required
def comment_like(request, pk):
    """"Функция лайка коммента"""
    user = request.user
    post = Post.objects.get(commentpost=pk)
    comments = Comment.objects.get(pk=pk)
    if not CommentRating.objects.filter(commentpk=comments).exists():
        comment = CommentRating(commentpk=comments)
        comment.save()
        comment.user.add(user)
        comment.like()
    elif user.pk in CommentRating.objects.filter(commentpk=comments).values_list('user', flat=True):
        comment = CommentRating.objects.get(commentpk=comments)
        comment.user.remove(user)
        comment.dislike()
    elif user.pk not in CommentRating.objects.filter(commentpk=comments).values_list('user', flat=True):
        comment = CommentRating.objects.get(commentpk=comments)
        comment.user.add(user)
        comment.like()
    return redirect(post.get_absolute_url())


@login_required
def deletecomment(request, pk):
    """"Функция удаления коммента"""
    comment = get_object_or_404(Comment, pk=pk)
    post = Post.objects.get(commentpost__pk=pk)
    if comment.user == request.user or post.author.user == request.user:
        comment.delete()
    else:
        raise PermissionDenied()
    return redirect(post.get_absolute_url())


@login_required
def subscribe(request, pk):
    """Функция подписки и оповещения о новых постах на подписанную категорию"""
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)
    message = 'Вы успешно подписались на рассылку постов на тему'

    return redirect(category.get_absolute_url())


@login_required
def unsubscribe(request, pk):
    """"Функция отписки и оповещения о новых постах на подписанную категорию"""
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)

    message = 'Вы отписались от рассылок постов на тему'
    return redirect(category.get_absolute_url())
