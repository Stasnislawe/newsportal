from django import forms
from django.core.exceptions import ValidationError
from .models import Post, Comment, Author
from datetime import date, datetime, timedelta
from crispy_forms.helper import FormHelper


class AuthorForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # self.helper = FormHelper()
        # self.helper.form_id = 'id-authorForm'
        # self.helper.form_class = 'form-horizontal'
        # self.helper.label_class = 'col-lg-3'
        # self.helper.field_class = 'col-lg-10'
        # self.helper.form_method = 'post'
        # self.helper.form_action = 'submit_survey'
        super(AuthorForm, self).__init__(*args, **kwargs)
        self.fields['photo'].label = 'Аватар'
        self.fields['username'].label = 'Никнейм'
        self.fields['description'].label = 'О себе'


    class Meta:
        model = Author

        fields = ['photo',
                  'username',
                  'description',
                  ]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        desc = cleaned_data.get("description")

        if username is not None and len(username) > 20:
            raise ValidationError(
                 "Имя пользователя не может быть больше 20 символов или быть пустым."
            )
        if username == desc:
            raise ValidationError(
                "Имя пользователя не должно быть идентичным описанию.")
        if desc[0].islower():
            raise ValidationError(
                "Описание должно начинаться с заглавной буквы.")
        if len(desc) < 30:
            raise ValidationError(
                "Минимальное количество символовов описания - 30")

        return cleaned_data


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('user', None)
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['image'].label = 'Изображение'
        self.fields['heading'].label = 'Наименование'
        self.fields['text'].label = 'Содержание до изображения'
        self.fields['text2'].label = 'Содержание после изображения'
        self.fields['posts_mtm'].empty_label = None
        self.fields['posts_mtm'].label = 'Категория'
        self.fields['post_type'].label = 'Тип поста'
        self.fields['draft'].label = 'Опубликовать'

    class Meta:
        model = Post

        fields = ['image',
                  'heading',
                  'text',
                  'text2',
                  'posts_mtm',
                  'post_type',
                  'draft']

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("text")
        heading = cleaned_data.get("heading")
        draft = cleaned_data.get("draft")
        author = self.author

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
                "Текст поста должен начинаться с заглавной буквы.")
        if len(text) < 30:
            raise ValidationError(
                "Минимальное количество символовов - 30")

        today = date.today()
        post_limit = Post.objects.filter(author__user=author, time_create__date=today).count()
        if post_limit >= 3:
            raise ValidationError({
                    'draft': "Вы можете публиковать только 3 поста в день!"
            })

        return cleaned_data


class CommentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].label = 'Содержание'

    class Meta:
        model = Comment
        fields = [
            'comment'
        ]

    def clean(self):
        cleaned_data = super().clean()
        comment = cleaned_data.get("comment")
        if comment[0].islower():
            raise ValidationError(
                "Комментарий должен начинаться с заглавной буквы.")

        return cleaned_data


