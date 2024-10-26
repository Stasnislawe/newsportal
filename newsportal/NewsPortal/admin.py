from django.contrib import admin
from .models import Author, Category, Post, Comment, PostCategory
#from modeltranslation.admin import TranslationAdmin

#class PostAdmin(admin.ModelAdmin):
#    list_display = ('heading', 'author', 'time_create', 'text')
#    list_filter = ('heading', 'author', 'time_create')

#class CategoryAdmin(TranslationAdmin):
    #model = Category

#class PostTranslAdmin(TranslationAdmin):
    #model = Post


admin.site.register(Author)
#admin.site.register(PostAdmin)
admin.site.register(Comment)
#admin.site.unregister(PostCategory)
admin.site.register(Post)
admin.site.register(Category)



