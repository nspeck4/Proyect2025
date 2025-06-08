from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OrganizationLevel, ApprovalFlow, ApproverRole
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import UserProfile

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'position', 'organization_level', 'is_staff')
    list_filter = ('organization_level', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'position', 'organization_level', 'boss')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'position', 'organization_level', 'boss', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(OrganizationLevel)
admin.site.register(ApprovalFlow)
admin.site.register(ApproverRole)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_short', 'address_short')
    search_fields = ('user__username', 'phone', 'address')

    def phone_short(self, obj):
        return obj.phone[:15] + '...' if len(obj.phone) > 15 else obj.phone

    phone_short.short_description = 'Teléfono'

    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address

    address_short.short_description = 'Dirección'