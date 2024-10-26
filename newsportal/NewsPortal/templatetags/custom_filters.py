from django import template


register = template.Library()

bad_words = [
   'Редиска', "редиска"
]

forbidden_words = [
   'Редиска', 'редиска', 'лох', 'Лох', 'Черт', 'черт'
]

@register.filter()
def censor(text):
   a = text
   for word in bad_words:
      a = a.replace(word, word[:1] + "*" * (len(word)-1))
   return a

@register.filter()
def censor2(text):
   a = text
   for word in forbidden_words:
      a = a.replace(word, word[:1] + "*" * (len(word)-2) + word[-1])
   return a




