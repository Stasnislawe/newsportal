from django_filters import FilterSet, DateFilter
from django import forms
from .models import Post

# Создаем свой набор фильтров для модели Product.
# FilterSet, который мы наследуем,
# должен чем-то напомнить знакомые вам Django дженерики.
class SearchFilter(FilterSet):
    # date = DateFilter(field_name='time_create', widget=forms.DateInput(attrs={'type': 'date'}), label='Поиск по дате',
    #                   lookup_expr='date__gte')
    class Meta:
        model = Post
        fields = {
            'heading': ['icontains'],
            # 'author': ['exact'],
        }