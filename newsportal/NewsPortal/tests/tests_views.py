from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Category, Comment, Author, Likes, Dislikes


class ViewsTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        # Создаем пользователей
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.author_user = User.objects.create_user(username='authoruser', password='testpass123')

        # Создаем группу authors и добавляем пользователя
        self.authors_group, created = Group.objects.get_or_create(name='authors')
        self.author_user.groups.add(self.authors_group)

        # Создаем авторов
        self.author = Author.objects.create(
            user=self.author_user,
            username='Test Author',
            description='Test author description'
        )

        # Создаем категорию
        self.category = Category.objects.create(name_category='Test Category')

        # Создаем пост
        self.post = Post.objects.create(
            heading='Test Post',
            text='This is a test post content that is long enough for validation.',
            text2='Additional text after image.',
            post_type='NW',
            draft=True,
            author=self.author
        )
        self.post.posts_mtm.add(self.category)

        # Создаем комментарий
        self.comment = Comment.objects.create(
            comment='Test comment',
            post=self.post,
            user=self.user
        )

    def test_post_detail_view(self):
        """Тест страницы деталей поста"""
        url = reverse('news_detail', args=[self.post.pk])
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post/post.html')
        self.assertEqual(response.context['post'], self.post)

    def test_post_detail_view_unpublished(self):
        """Тест доступа к неопубликованному посту"""
        unpublished_post = Post.objects.create(
            heading='Unpublished Post',
            text='Unpublished content that is long enough',
            draft=False,
            author=self.author
        )
        unpublished_post.posts_mtm.add(self.category)

        # Неавторизованный пользователь
        url = reverse('news_detail', args=[unpublished_post.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Обычный пользователь
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Permission denied

        # Автор поста
        self.client.force_login(self.author_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_only_news_view(self):
        """Тест страницы только с новостями"""
        url = reverse('news')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news.html')

    def test_only_articles_view(self):
        """Тест страницы только со статьями"""
        url = reverse('art')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'art.html')

    def test_category_list_view(self):
        """Тест страницы категории"""
        url = reverse('category_list', args=[self.category.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categories/category.html')
        self.assertIn('category', response.context)

    def test_like_function(self):
        """Тест функции лайка"""
        self.client.force_login(self.user)
        url = reverse('like', args=[self.post.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Проверяем, что лайк добавился
        like_exists = Likes.objects.filter(rating=self.post, user=self.user).exists()
        self.assertTrue(like_exists)

    def test_dislike_function(self):
        """Тест функции дизлайка"""
        self.client.force_login(self.user)
        url = reverse('dislike', args=[self.post.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Проверяем, что дизлайк добавился
        dislike_exists = Dislikes.objects.filter(rating=self.post, user=self.user).exists()
        self.assertTrue(dislike_exists)

    def test_comment_function(self):
        """Тест функции комментария"""
        self.client.force_login(self.user)
        url = reverse('comment_add', args=[self.post.pk])

        data = {'comment': 'New test comment'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Redirect

        # Проверяем, что комментарий добавился
        comment_exists = Comment.objects.filter(
            post=self.post,
            user=self.user,
            comment='New test comment'
        ).exists()
        self.assertTrue(comment_exists)

    def test_subscribe_function(self):
        """Тест функции подписки"""
        self.client.force_login(self.user)
        url = reverse('subscribe', args=[self.category.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Проверяем, что пользователь подписался
        self.assertTrue(self.category.subscribers.filter(pk=self.user.pk).exists())

    def test_unsubscribe_function(self):
        """Тест функции отписки"""
        # Сначала подписываемся
        self.category.subscribers.add(self.user)

        self.client.force_login(self.user)
        url = reverse('unsubscribe', args=[self.category.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Проверяем, что пользователь отписался
        self.assertFalse(self.category.subscribers.filter(pk=self.user.pk).exists())

    def test_my_posts_view(self):
        """Тест страницы моих постов"""
        # Добавляем права пользователю
        content_type = ContentType.objects.get_for_model(Post)
        post_permissions = Permission.objects.filter(content_type=content_type)
        for perm in post_permissions:
            self.author_user.user_permissions.add(perm)

        self.client.force_login(self.author_user)
        url = reverse('myviews')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post/myposts.html')


class AuthViewsTest(TestCase):

    def setUp(self):
        # Создаем пользователей с разными правами
        self.user = User.objects.create_user(username='testuser', password='testpass123')

        self.author_user = User.objects.create_user(username='authoruser', password='testpass123')

        # Добавляем права автора
        content_type = ContentType.objects.get_for_model(Post)
        post_permissions = Permission.objects.filter(content_type=content_type)
        for perm in post_permissions:
            self.author_user.user_permissions.add(perm)

        # Создаем авторов
        self.author = Author.objects.create(
            user=self.author_user,
            username='Test Author',
            description='Test author description'
        )

        # Создаем пост
        self.post = Post.objects.create(
            heading='Test Post',
            text='Test content',
            author=self.author,
            draft=True
        )

    def test_post_create_view_access(self):
        """Тест доступа к созданию поста"""
        url = reverse('news_create')

        # Неавторизованный пользователь
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Обычный пользователь без прав
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Permission denied

        # Автор с правами
        self.client.force_login(self.author_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_view_access(self):
        """Тест доступа к редактированию поста"""
        url = reverse('news_edit', args=[self.post.pk])

        # Неавторизованный пользователь
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Обычный пользователь без прав
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Автор поста
        self.client.force_login(self.author_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_delete_view_access(self):
        """Тест доступа к удалению поста"""
        url = reverse('news_delete', args=[self.post.pk])

        # Неавторизованный пользователь
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Обычный пользователь без прав
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Автор поста
        self.client.force_login(self.author_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class FormViewsTest(TestCase):

    def setUp(self):
        self.author_user = User.objects.create_user(username='authoruser', password='testpass123')

        # Добавляем права
        content_type = ContentType.objects.get_for_model(Post)
        post_permissions = Permission.objects.filter(content_type=content_type)
        for perm in post_permissions:
            self.author_user.user_permissions.add(perm)

        self.author = Author.objects.create(
            user=self.author_user,
            username='Test Author',
            description='Test description'
        )

        self.category = Category.objects.create(name_category='Test Category')

    def test_post_create_form(self):
        """Тест создания поста через форму"""
        self.client.force_login(self.author_user)
        url = reverse('news_create')

        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content" * 100,
            content_type="image/jpeg"
        )

        data = {
            'heading': 'New Test Post With Capital Letter',
            'text': 'This is a test post content that is long enough for validation and starts with capital.',
            'text2': 'Additional text after image for testing purposes.',
            'posts_mtm': [self.category.pk],
            'post_type': 'NW',
            'draft': True,
        }

        response = self.client.post(url, {**data, 'image': image})

        # Проверяем редирект после успешного создания
        self.assertEqual(response.status_code, 302)

        # Проверяем, что пост создалс
        post_exists = Post.objects.filter(
            heading='New Test Post With Capital Letter',
            author=self.author
        ).exists()
        self.assertTrue(post_exists)


class PaginationTest(TestCase):

    def setUp(self):
        # Создаем несколько постов для тестирования пагинации
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.author = Author.objects.create(
            user=self.user,
            username='Test Author',
            description='Test description'
        )

        # Создаем 15 постов (больше чем paginate_by=10)
        for i in range(15):
            Post.objects.create(
                heading=f'Test Post {i}',
                text=f'Content {i}',
                author=self.author,
                draft=True
            )

    def test_pagination_on_posts_list(self):
        """Тест пагинации на главной странице"""
        url = reverse('news_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['posts']), 8)  # paginate_by=8

    def test_pagination_on_news_page(self):
        """Тест пагинации на странице новостей"""
        url = reverse('news')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['onews']), 10)  # paginate_by=10