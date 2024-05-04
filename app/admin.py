from django.contrib import admin
from .models import URLRedirect

class URLRedirectAdmin(admin.ModelAdmin):
    list_display = ('url', 'hit_count')

admin.site.register(URLRedirect, URLRedirectAdmin)