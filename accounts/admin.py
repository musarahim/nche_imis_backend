from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import (AdminPasswordChangeForm, UserChangeForm,
                          UserCreationForm)
import pyotp
from trench.models import MFAMethod

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form that creates MFAMethod."""
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Create MFAMethod for the new user
            MFAMethod.objects.get_or_create(
                user=user,
                name='email',
                defaults={
                    'is_active': True,
                    'is_primary': True,
                    'secret': pyotp.random_base32(length=32)
                }
            )
        return user

# Register your models here.
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    form = UserChangeForm
    add_form = CustomUserCreationForm  # Use our custom form
    change_password_form = AdminPasswordChangeForm
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        ('Personal info', {'fields': ('first_name', 'last_name','other_names','phone','alternative_phone_number','profile_pic')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined','account_expiry_date')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Personal info', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'other_names', 'phone', 'alternative_phone_number', 'profile_pic'),
        }),
        ('Permissions', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Account Settings', {
            'classes': ('wide',),
            'fields': ('account_expiry_date',),
        }),
    )

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
