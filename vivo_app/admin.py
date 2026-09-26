from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('title', 'institution', 'department', 'phone', 'orcid_id', 'email_confirmed')


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_institution')
    list_select_related = ('profile',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__institution')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__email_confirmed')

    def get_institution(self, instance):
        return instance.profile.institution

    get_institution.short_description = 'Institution'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Unregister the default User admin and register our custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Register UserProfile separately as well for direct access
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'department', 'email_confirmed')
    list_filter = ('email_confirmed', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'institution', 'department', 'orcid_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('user', 'email_confirmed')}),
        ('Professional Information', {'fields': ('title', 'institution', 'department', 'phone', 'orcid_id')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
