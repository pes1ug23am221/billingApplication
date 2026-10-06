from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, InviteToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'invited_by', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Invite Info', {'fields': ('invited_by',)}),
    )


@admin.register(InviteToken)
class InviteTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'created_by', 'used_by', 'expires_at', 'is_used', 'created_at']
    list_filter = ['is_used']
    readonly_fields = ['token', 'created_at']
    search_fields = ['created_by__username', 'used_by__username']
