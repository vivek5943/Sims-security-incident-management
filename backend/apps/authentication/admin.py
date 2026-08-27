from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.authentication.models import User, Role, LoginAttempt

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['role_id', 'role_name']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['user_id', 'full_name', 'email', 'role', 'status', 'created_at']
    list_filter   = ['role', 'status']
    search_fields = ['full_name', 'email']
    ordering      = ['-created_at']
    fieldsets = (
        (None,             {'fields': ('email', 'password')}),
        ('Personal Info',  {'fields': ('full_name',)}),
        ('Role & Status',  {'fields': ('role', 'status')}),
        ('Permissions',    {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email','full_name','password1','password2','role')}),
    )

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display  = ['email', 'ip_address', 'success', 'attempted_at']
    list_filter   = ['success']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['email', 'ip_address', 'success', 'attempted_at']
    def has_add_permission(self, request):    return False
    def has_change_permission(self, r, o=None): return False
