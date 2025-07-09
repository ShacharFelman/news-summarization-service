from django.contrib import admin

from articles.models import Article


class ArticleAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'title')  # Add other fields as needed


admin.site.register(Article, ArticleAdmin)
