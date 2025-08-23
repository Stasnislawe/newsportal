from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from ..models import Author, Category, Post
from ..forms import AuthorForm, PostForm, CommentForm


class AuthorFormTest(TestCase):

    def setUp(self):
        # Создаем пользователя для связи с автором
        self.user = User.objects.create_user(username='testuser', password='12345')
        # Валидные данные для формы
        self.valid_data = {
            'username': 'ValidUsername',
            'description': 'Это очень длинное и корректное описание профиля, которое точно больше 30 символов.',
        }
        self.image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

    def test_author_form_valid_data(self):
        """Тест формы AuthorForm с валидными данными"""
        form = AuthorForm(data=self.valid_data, files={'photo': self.image})
        print(f"AuthorForm errors: {form.errors}")  # Добавляем вывод ошибок для диагностики
        self.assertTrue(form.is_valid())

    def test_author_form_invalid_username_length(self):
        """Тест формы AuthorForm с слишком длинным именем пользователя"""
        invalid_data = self.valid_data.copy()
        invalid_data['username'] = 'ОченьДлинноеИмяПользователя'
        form = AuthorForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_author_form_username_equals_description(self):
        """Тест формы AuthorForm, когда имя и описание одинаковы"""
        invalid_data = {
            'username': 'Одинаковое',
            'description': 'Одинаковое',
        }
        form = AuthorForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_author_form_description_starts_lowercase(self):
        """Тест формы AuthorForm, когда описание начинается с маленькой буквы"""
        invalid_data = self.valid_data.copy()
        invalid_data['description'] = 'описание начинается с маленькой буквы и достаточно длинное.'
        form = AuthorForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_author_form_short_description(self):
        """Тест формы AuthorForm с слишком коротким описанием"""
        invalid_data = self.valid_data.copy()
        invalid_data['description'] = 'Короткое.'
        form = AuthorForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class PostFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(
            user=self.user,
            username='author',
            description='Длинное описание для теста автора.'
        )
        self.category = Category.objects.create(name_category='ТестКатегория')

        self.valid_data = {
            'heading': 'Корректный Заголовок Поста',
            'text': 'Это основной текст поста, который точно длиннее тридцати символов и должен пройти валидацию.',
            'text2': 'Дополнительный текст после изображения для тестирования формы.',
            'posts_mtm': self.category.id,  # ManyToMany поле передается как список ID
            'post_type': 'NW',
            'draft': True,
        }
        self.image = SimpleUploadedFile("post.jpg", b"file_content", content_type="image/jpeg")

    def test_post_form_valid_data(self):
        """Тест формы PostForm с валидными данными"""
        form = PostForm(data=self.valid_data, files={'image': self.image}, user=self.user)
        print(f"PostForm errors: {form.errors}")  # Добавляем вывод ошибок для диагностики
        self.assertTrue(form.is_valid())

    def test_post_form_long_heading(self):
        """Тест формы PostForm с слишком длинным заголовком"""
        invalid_data = self.valid_data.copy()
        invalid_data['heading'] = 'О' * 101  # Заголовок из 101 символа
        form = PostForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('heading', form.errors)

    def test_post_form_heading_equals_text(self):
        """Тест формы PostForm, когда заголовок идентичен тексту"""
        invalid_data = self.valid_data.copy()
        invalid_data['text'] = invalid_data['heading']
        form = PostForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_post_form_heading_starts_lowercase(self):
        """Тест формы PostForm, когда заголовок начинается с маленькой буквы"""
        invalid_data = self.valid_data.copy()
        invalid_data['heading'] = 'неверный заголовок'
        form = PostForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_post_form_text_starts_lowercase(self):
        """Тест формы PostForm, когда текст начинается с маленькой буквы"""
        invalid_data = self.valid_data.copy()
        invalid_data['text'] = 'неверный текст, но достаточно длинный для прохождения проверки на минимальную длину.'
        form = PostForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_post_form_short_text(self):
        """Тест формы PostForm с слишком коротким текстом"""
        invalid_data = self.valid_data.copy()
        invalid_data['text'] = 'Короткий текст.'
        form = PostForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_post_form_daily_limit(self):
        """Тест формы PostForm на превышение лимита постов в день"""
        # Создаем 3 поста от этого пользователя сегодня
        for i in range(3):
            Post.objects.create(
                heading=f'Пост {i}',
                text='Достаточно длинный текст для поста, чтобы пройти валидацию по минимальной длине.',
                author=self.author,
                post_type='NW'
            )

        form = PostForm(data=self.valid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('draft', form.errors)
        self.assertIn('3 поста в день', form.errors['draft'][0])


class CommentFormTest(TestCase):

    def test_comment_form_valid_data(self):
        """Тест формы CommentForm с валидными данными"""
        form = CommentForm(data={'comment': 'Валидный комментарий начинается с большой буквы.'})
        self.assertTrue(form.is_valid())

    def test_comment_form_starts_lowercase(self):
        """Тест формы CommentForm, когда комментарий начинается с маленькой буквы"""
        form = CommentForm(data={'comment': 'невалидный комментарий с маленькой буквы.'})
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)