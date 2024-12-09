from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Chat(models.Model):
    DIALOG = 'D'
    CHAT = 'C'
    CHAT_TYPE_CHOICES = [
        (DIALOG, 'Dialog'),
        (CHAT, 'Chat')
    ]

    type = models.CharField(
        max_length=1,
        choices=CHAT_TYPE_CHOICES,
        default=DIALOG,
        verbose_name='Тип'
    )
    members = models.ManyToManyField(User, verbose_name="Участник")

    def get_absolute_url(self):
        return reverse('messages', args=[str(self.id)])


class Message(models.Model):
    chat = models.ForeignKey(Chat, verbose_name="Чат", on_delete=models.CASCADE)
    author = models.ForeignKey(User, verbose_name="Пользователь", related_name='message_author', on_delete=models.CASCADE)
    message = models.TextField(verbose_name="Сообщение", max_length=256)
    pub_date = models.DateTimeField(verbose_name='Дата сообщения', auto_now_add=True)
    is_readed = models.BooleanField(verbose_name='Прочитано', default=False)

    class Meta:
        ordering = ['pub_date']

    def __str__(self):
        return self.message