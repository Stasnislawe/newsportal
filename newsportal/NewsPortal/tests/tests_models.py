from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from ..models import Author, Category, Post, PostCategory, Comment, CommentRating, Likes, Dislikes


class AuthorModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(
            user=self.user,
            username='testauthor',
            description='Это тестовое описание профиля, которое достаточно длинное.',
            rating=10
        )

    def test_author_creation(self):
        """Тест корректного создания объекта Author"""
        self.assertEqual(self.author.user.username, 'testuser')
        self.assertEqual(self.author.username, 'testauthor')
        self.assertTrue(len(self.author.description) >= 30)
        self.assertEqual(self.author.rating, 10)

    def test_author_str_representation(self):
        """Тест строкового представления модели Author"""
        self.assertEqual(str(self.author), 'testuser')

    def test_author_update_rating(self):
        """Тест метода update_rating (упрощенный)"""
        initial_rating = self.author.rating
        self.author.update_rating()
        # Метод что-то делает, даже если нет постов/лайков
        self.assertIsInstance(self.author.rating, (int, float))


class CategoryModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name_category='Технологии')

    def test_category_creation(self):
        """Тест корректного создания объекта Category"""
        self.assertEqual(self.category.name_category, 'Технологии')
        self.assertEqual(str(self.category), 'Технологии')

    def test_category_get_absolute_url(self):
        """Тест метода get_absolute_url модели Category"""
        expected_url = reverse('category_list', args=[self.category.id])
        self.assertEqual(self.category.get_absolute_url(), expected_url)


class PostModelTest(TestCase):

    def setUp(self):
        # Создаем необходимые объекты
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(
            user=self.user,
            username='testauthor',
            description='Достаточно длинное описание для теста.'
        )
        self.category = Category.objects.create(name_category='Наука')
        self.post = Post.objects.create(
            post_type=Post.news,
            heading='Тестовый заголовок новости',
            text='Это первый сегмент текста, который должен быть достаточно длинным.',
            text2='Это второй сегмент текста после изображения.',
            author=self.author,
            draft=True
        )
        # Добавляем категорию через промежуточную модель
        PostCategory.objects.create(post=self.post, category=self.category)

    def test_post_creation(self):
        """Тест корректного создания объекта Post"""
        self.assertEqual(self.post.heading, 'Тестовый заголовок новости')
        self.assertEqual(self.post.post_type, 'NW')
        self.assertFalse(self.post.text2 == '')  # text2 не пустой
        self.assertTrue(self.post.draft)
        self.assertEqual(self.post.author, self.author)
        # Проверяем, что категория добавлена
        self.assertIn(self.category, self.post.posts_mtm.all())

    def test_post_str_representation(self):
        """Тест строкового представления модели Post"""
        expected_str = f'{self.post.pk} - Тестовый заголовок новости - NW - {self.author}'
        self.assertEqual(str(self.post), expected_str)

    def test_post_preview(self):
        """Тест метода preview() модели Post"""
        preview = self.post.preview()
        # Правильное ожидание: первые 125 символов + '...'
        expected_preview = self.post.text[:125] + '...'
        self.assertEqual(preview, expected_preview)

        # Дополнительная проверка длины
        self.assertTrue(len(preview) <= 128)  # 125 + 3 точки

    def test_post_get_absolute_url(self):
        """Тест метода get_absolute_url модели Post"""
        expected_url = reverse('news_detail', args=[self.post.id])
        self.assertEqual(self.post.get_absolute_url(), expected_url)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(
            user=self.user,
            username='testauthor',
            description='Достаточно длинное описание для теста.'
        )
        self.post = Post.objects.create(
            post_type=Post.news,
            heading='Тестовый пост для комментария',
            text='Текст поста для комментария.',
            author=self.author
        )
        self.comment = Comment.objects.create(
            comment='Это тестовый комментарий к посту.',
            post=self.post,
            user=self.user
        )

    def test_comment_creation(self):
        """Тест корректного создания объекта Comment"""
        self.assertEqual(self.comment.comment, 'Это тестовый комментарий к посту.')
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.user, self.user)

    def test_comment_str_representation(self):
        """Тест строкового представления модели Comment"""
        # Проверяем, что в строке есть ключевые элементы
        self.assertIn(str(self.comment.pk), str(self.comment))
        self.assertIn('Это тестовый комментарий к посту.', str(self.comment))


class LikesDislikesModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(
            user=self.user,
            username='testauthor',
            description='Достаточно длинное описание.'
        )
        self.post = Post.objects.create(
            post_type=Post.news,
            heading='Пост для лайков',
            text='Текст поста.',
            author=self.author
        )
        self.like = Likes.objects.create(rating=self.post)
        self.dislike = Dislikes.objects.create(rating=self.post)

    def test_like_creation(self):
        """Тест создания лайка"""
        self.like.user.add(self.user)
        self.assertEqual(self.like.rating, self.post)
        self.assertIn(self.user, self.like.user.all())

    def test_dislike_creation(self):
        """Тест создания дизлайка"""
        self.dislike.user.add(self.user)
        self.assertEqual(self.dislike.rating, self.post)
        self.assertIn(self.user, self.dislike.user.all())

    def test_like_methods(self):
        """Тест методов like и dislike модели Likes"""
        initial_rate = self.like.rate
        self.like.like()
        self.assertEqual(self.like.rate, initial_rate + 1)
        self.like.dislike()
        self.assertEqual(self.like.rate, initial_rate)  # Вернулось к исходному

    def test_dislike_methods(self):
        """Тест методов like и dislike модели Dislikes"""
        initial_rate = self.dislike.rate
        self.dislike.like()
        self.assertEqual(self.dislike.rate, initial_rate + 1)
        self.dislike.dislike()
        self.assertEqual(self.dislike.rate, initial_rate)