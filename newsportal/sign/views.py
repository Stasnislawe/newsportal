from django.contrib.auth.models import User
from django.http import request
from django.views.generic.edit import CreateView
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
        kwargs['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        kwargs['count_mynews'] = Post.objects.filter(author__user__username=self.request.user)
        kwargs['rating'] = Author.objects.filter(user__username=self.request.user)
        return super().get_context_data(**kwargs)


class CreateAuthor(CreateView):
    model = Author
    form_class = AuthorForm
    success_url = 'index'
    template_name = 'authorcreate.html'

    def form_valid(self, form):
        self.object = self.form_class
        self.object.author = self.request.user.pk
        self.object.save()
        return super().form_valid(form)