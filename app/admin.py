from django.contrib import admin
from .models import Bookmark, URLRedirect

class URLRedirectAdmin(admin.ModelAdmin):
    list_display = ('url', 'hit_count')


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'organ_id', 'created_at')


admin.site.register(URLRedirect, URLRedirectAdmin)
admin.site.register(Bookmark, BookmarkAdmin)