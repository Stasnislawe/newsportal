from django import forms
from django.core.exceptions import ValidationError
from .models import Post
from datetime import date, datetime, timedelta


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['heading'].label = 'Наименование'
        self.fields['text'].label = 'Содержание'
        self.fields['posts_mtm'].empty_label = None
        self.fields['posts_mtm'].label = 'Категория'
        self.fields['author'].label = 'Автор'




    class Meta:
        model = Post

        fields = ['heading',
                  'text',
                  'author',
                  'posts_mtm']


    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("text")
        heading = cleaned_data.get("heading")
        author = cleaned_data.get("author")


        if heading is not None and len(heading) > 100:
            raise ValidationError({
                "title": "Заголовок не может быть более 100 символов."
            })
        if heading == text:
            raise ValidationError(
                "Заголовок не должен быть идентичным тексту статьи.")
        if heading[0].islower():
            raise ValidationError(
                "Заголовок должен начинаться с заглавной буквы.")
        if text[0].islower():
            raise ValidationError(
                "Текст статьи должен начинаться с заглавной буквы.")


        today = date.today()
        post_limit = Post.objects.filter(author=author, time_create__date=today).count()
        if post_limit >= 3:
            raise ValidationError({
                    'text': "Вы можете публиковать только 3 поста в день!"
            })

        return cleaned_data

