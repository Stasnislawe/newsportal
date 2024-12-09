from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, CheckConstraint, Count
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.core.cache import cache


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_admin')
    username = models.CharField(max_length=20)
    description = models.CharField(max_length=250, default='Пользователь еще не добавил описание своего профиля')
    rating = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='authors/', default='nophoto.jpg')

    def __str__(self):
        return self.user.username

    def update_rating(self):
        post_likes_rating = self.posts.aggregate(pl=Coalesce(Sum('post_likes__rate'), 0)).get('pl')
        post_dislikes_rating = self.posts.aggregate(pd=Coalesce(Sum('post_dislikes__rate'), 0)).get('pd')
        count_comments = self.posts.aggregate(cnt=Coalesce(Count('commentpost'), 0)).get('cnt')
        rate_comments = (self.posts.aggregate(rc=Coalesce(Sum('author__user__com_rate_user__rating'), 0)).get('rc'))
        self.rating = post_likes_rating * 3 - post_dislikes_rating + count_comments + (rate_comments/3)
        self.save()


class Category(models.Model):
    name_category = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(User, related_name='categories')

    def __str__(self):
        return self.name_category

    def get_absolute_url(self):
        return reverse('category_list', args=[str(self.id)])


class Post(models.Model):
    article = 'AR'
    news = 'NW'

    POS = [
        (article, 'Статья'),
        (news, 'Новость'),
    ]

    post_type = models.CharField(max_length=2, choices=POS, default='NW')
    image = models.ImageField(upload_to='images/%Y/%m/%d/', default='nophoto.jpg')
    time_create = models.DateTimeField(auto_now_add=True)
    heading = models.CharField(max_length=255, default='Название отсутсвует')
    text = models.TextField(verbose_name='Текст до изображения')
    text2 = models.TextField(verbose_name='Текст после изображения', blank=True)
    draft = models.BooleanField(verbose_name='Опубликовать', default=True)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name ='posts')
    posts_mtm = models.ManyToManyField(Category, through='PostCategory')

    def preview(self):
        return self.text[0:125] + '...'

    def __str__(self):
        return f'{self.pk} - {self.heading} - {self.post_type} - {self.author}'

    def get_absolute_url(self):
        return reverse('news_detail', args=[str(self.id)])

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)  # сначала вызываем метод родителя, чтобы объект сохранился
    #     cache.delete(f'product-{self.pk}')  # затем удаляем его из кэша, чтобы сбросить его


class Likes(models.Model):
    rate = models.PositiveIntegerField(default=0)
    user = models.ManyToManyField(User, related_name='user_likes')
    rating = models.OneToOneField(Post, related_name='post_likes', on_delete=models.CASCADE)

    def like(self):
        self.rate += 1
        self.save()

    def dislike(self):
        self.rate -= 1
        self.save()

    def preview(self):
        return self.rate


class Dislikes(models.Model):
    rate = models.PositiveIntegerField(default=0)
    user = models.ManyToManyField(User, related_name='user_dislikes')
    rating = models.OneToOneField(Post, related_name='post_dislikes', on_delete=models.CASCADE)

    def like(self):
        self.rate += 1
        self.save()

    def dislike(self):
        self.rate -= 1
        self.save()

    def preview(self):
        return self.rate


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Comment(models.Model):
    comment = models.CharField(max_length=255)
    time_create_comment = models.DateTimeField(auto_now_add=True)

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='commentpost')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return '{} {} {} {} {}'.format(self.pk, self.comment, self.time_create_comment, self.post, self.user)


class CommentRating(models.Model):
    commentpk = models.OneToOneField(Comment, on_delete=models.CASCADE, related_name='commentrating')
    user = models.ManyToManyField(User, related_name='com_rate_user')
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

