from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    #поля которые будут видны в списке объектов
    list_display = ['title', 'slug', 'author', 'publish', 'updated', 'status']
    #поля по которым сможем фильтровать
    list_filter = ['status', 'created', 'publish', 'author']
    #поля по которым сможем выполнять поиск
    search_fields = ['title', 'body']
    #предварительное заполенение поля
    prepopulated_fields = {'slug': ('title',)}
    #вместо выпадающего списка, поле ввода
    raw_id_fields = ['author']
    #для навигационных ссылок для навигации по иерархии дат
    date_hierarchy = 'publish'
    #упорядочивание по столбцам на сайте админки
    ordering = ['status', 'publish']

