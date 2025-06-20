from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import (AdminPasswordChangeForm, UserChangeForm,
                          UserCreationForm)

from .models import User

# Register your models here.
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    # Forms loaded from `unfold.forms`
   # list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser')
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
