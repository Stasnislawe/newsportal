from django.contrib.auth.models import User
from django.http import request
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from NewsPortal.models import Post, Author

from .models import BaseRegisterForm
from NewsPortal.forms import AuthorForm


@login_required
def upgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)
    return redirect('/sign/index')


@login_required
def disupgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if request.user.groups.filter(name='authors').exists():
        authors_group.user_set.remove(user)
    return redirect('/sign/index')


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        if Author.objects.filter(user__username=self.request.user).exists():
            self.req_author = Author.objects.get(user__username=self.request.user)
            self.req_author.update_rating()
            kwargs['rating'] = self.req_author

        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        kwargs['count_mynews'] = Post.objects.filter(author__user__username=self.request.user)
        return super().get_context_data(**kwargs)


class CreateAuthor(CreateView):
    model = Author
    form_class = AuthorForm
    success_url = reverse_lazy('index')
    template_name = 'authorcreate.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        upgrade_me(self.request)
        return super().form_valid(form)


class EditAuthor(UpdateView):
    model = Author
    form_class = AuthorForm
    success_url = reverse_lazy('index')
    template_name = 'authoredit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = Author.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)