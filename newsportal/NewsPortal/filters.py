from django_filters import FilterSet, DateFilter
from django import forms
from .models import Post


class SearchFilter(FilterSet):

    class Meta:
        model = Post
        fields = {
            'heading': ['icontains'],
        }