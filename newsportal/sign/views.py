from django.contrib.auth.models import User
from django.http import request, JsonResponse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from NewsPortal.models import Post, Author
from django.contrib import messages
from django.db import IntegrityError
from .models import BaseRegisterForm
from NewsPortal.forms import AuthorForm


@login_required
def upgrade_me(request):
    """Функция получения роли 'Автор'"""
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)
        messages.success(request, 'Теперь вы автор!')
    return redirect('index')


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = reverse_lazy('login')


# views.py
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'account/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Проверяем, является ли пользователь автором
            is_author = self.request.user.groups.filter(name='authors').exists()
            context['is_author'] = is_author
            context['is_not_author'] = not is_author

            # Проверяем, есть ли запись автора
            if Author.objects.filter(user=self.request.user).exists():
                author = Author.objects.get(user=self.request.user)
                author.update_rating()
                context['author'] = author
                context['rating'] = author.rating

            # Подсчёт постов
            context['count_mynews'] = Post.objects.filter(author__user=self.request.user).count()

        except Exception as e:
            # Логируем ошибку
            print(f"Error in IndexView: {e}")
            context['is_author'] = False
            context['is_not_author'] = True
            context['count_mynews'] = 0

        return context

    def post(self, request, *args, **kwargs):
        """Обработка AJAX-запроса на сохранение данных"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.handle_ajax_request(request)

        # Обычная POST-обработка (если нужно)
        return super().get(request, *args, **kwargs)

    def handle_ajax_request(self, request):
        """Обработка AJAX-запроса"""
        author = None
        if Author.objects.filter(user=request.user).exists():
            author = Author.objects.get(user=request.user)
            form = AuthorForm(request.POST, request.FILES, instance=author)
        else:
            form = AuthorForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                author_instance = form.save(commit=False)
                author_instance.user = request.user
                author_instance.save()

                # Обновляем username пользователя
                if 'username' in form.cleaned_data:
                    request.user.username = form.cleaned_data['username']
                    request.user.save()

                messages.success(request, 'Данные успешно сохранены!')
                return JsonResponse({'success': True, 'message': 'Данные сохранены'})

            except IntegrityError:
                return JsonResponse({'success': False, 'error': 'Ошибка сохранения'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def save_author_data(request):
    """Отдельная view для сохранения данных автора"""
    if request.method == 'POST':
        author = None
        if Author.objects.filter(user=request.user).exists():
            author = Author.objects.get(user=request.user)
            form = AuthorForm(request.POST, request.FILES, instance=author)
        else:
            form = AuthorForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                author_instance = form.save(commit=False)
                author_instance.user = request.user
                author_instance.save()

                # Обновляем username пользователя
                if 'username' in form.cleaned_data:
                    request.user.username = form.cleaned_data['username']
                    request.user.save()

                # Добавляем пользователя в группу авторов
                authors_group = Group.objects.get(name='authors')
                if not request.user.groups.filter(name='authors').exists():
                    authors_group.user_set.add(request.user)
                    messages.success(request, 'Вы стали автором! Данные успешно сохранены!')
                else:
                    messages.success(request, 'Данные успешно сохранены!')

                return redirect('index')

            except IntegrityError:
                messages.error(request, 'Ошибка сохранения данных')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')

        return redirect('index')


@login_required
def delete_author_profile(request):
    """Удаление профиля автора"""
    if Author.objects.filter(user=request.user).exists():
        Author.objects.filter(user=request.user).delete()
        messages.success(request, 'Профиль автора удален')

    # Убираем из группы авторов
    if request.user.groups.filter(name='authors').exists():
        authors_group = Group.objects.get(name='authors')
        authors_group.user_set.remove(request.user)
        messages.info(request, 'Вы больше не автор')

    return redirect('index')