from django.contrib import admin
from .models import Post, Comment
# Register your models here.
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at')  # Columns to show
    list_filter = ('created_at', 'author')  # Sidebar filters
    search_fields = ('title', 'content')    # Search bar functionality
    prepopulated_fields = {'slug': ('title',)}  # Auto-fill slug from title
    ordering = ('-created_at',)


admin.site.register(Post , PostAdmin)
admin.site.register(Comment)