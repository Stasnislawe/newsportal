from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.core.cache import cache

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='authors/', default='nophoto.jpg')

    def __str__(self):
        return self.user.username

    def update_rating(self):
        post_rating = self.posts.aggregate(pr=Coalesce(Sum('rating_post'), 0)).get('pr')
        comment_rating = self.user.comments.aggregate(cr=Coalesce(Sum('rating_comment'), 0)).get('cr')
        posts_comment_rating = self.posts.aggregate(pcr=Coalesce(Sum('comment__rating_comment'), 0)).get('pcr')

        self.rating = post_rating * 3 + comment_rating + posts_comment_rating
        self.save()

class Category(models.Model):
    name_category = models.CharField(max_length=100, unique = True)
    subscribers = models.ManyToManyField(User, blank=True, null=True, related_name='categories')

    def __str__(self):
        return self.name_category

class Post(models.Model):
    article = 'AR'
    news = 'NW'

    POS = [
        (article, 'Статья'),
        (news, 'Новость'),
    ]

    post_type = models.CharField(max_length = 2, choices = POS, default='NW')
    image = models.ImageField(upload_to='images/%Y/%m/%d/', default='nophoto.jpg')
    time_create = models.DateTimeField(auto_now_add = True)
    heading = models.CharField(max_length = 255, default = 'Название отсутсвует')
    text = models.TextField(verbose_name='Текст до изображения')
    text2 = models.TextField(verbose_name='Текст после изображения', blank=True)
    rating_post = models.IntegerField(default=0)

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name ='posts')
    posts_mtm = models.ManyToManyField(Category, through = 'PostCategory')


    def like(self):
        self.rating_post += 1
        self.save()

    def dislike(self):
        self.rating_post -= 1
        self.save()

    def preview(self):
        return self.text[0:125] + '...'

    def __str__(self):
        return f'{self.heading} {self.post_type}'

    def get_absolute_url(self):
        return reverse('news_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # сначала вызываем метод родителя, чтобы объект сохранился
        cache.delete(f'product-{self.pk}')  # затем удаляем его из кэша, чтобы сбросить его

class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete = models.CASCADE)
    category = models.ForeignKey(Category, on_delete = models.CASCADE)

class Comment(models.Model):
    comment = models.CharField(max_length = 255)
    time_create_comment = models.DateTimeField(auto_now_add=True)
    rating_comment = models.IntegerField(default = 0)

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name ='comments')

    def like(self):
        self.rating_comment += 1
        self.save()

    def dislike(self):
        self.rating_comment -= 1
        self.save()

    def __str__(self):
        return self.comment, self.time_create_comment, self.rating_comment, self.post, self.user

