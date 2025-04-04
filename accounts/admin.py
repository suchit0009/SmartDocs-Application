from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('profile_picture',  'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('profile_picture',  'phone_number')}),
    )
    list_display = UserAdmin.list_display + ('profile_picture',  'phone_number')
    search_fields = UserAdmin.search_fields + ('phone_number',)  # Add phone number to search fields if desired

admin.site.register(CustomUser, CustomUserAdmin)


