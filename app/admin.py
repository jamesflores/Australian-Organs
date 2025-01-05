from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Bookmark, URLRedirect


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)


class URLRedirectAdmin(admin.ModelAdmin):
    list_display = ('url', 'hit_count')


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'organ_id', 'created_at')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(URLRedirect, URLRedirectAdmin)
admin.site.register(Bookmark, BookmarkAdmin)