from django.contrib import admin
from .models import SharedDocument
from documents.models import Document
from django.contrib.auth.models import User

class SharedDocumentAdmin(admin.ModelAdmin):
    list_display = ('document', 'shared_by', 'shared_with', 'permission', 'shared_at')
    list_filter = ('permission', 'shared_at', 'shared_by', 'shared_with')
    search_fields = ('document__title', 'shared_by__username', 'shared_with__username')

    # Optionally add this to make the `get_permission_display()` work in the list view
    def get_permission_display_column(self, obj):
        return obj.get_permission_display()

    get_permission_display_column.short_description = 'Permission'

    # Add `get_permission_display_column` to the list_display tuple
    list_display = ('document', 'shared_by', 'shared_with', 'get_permission_display_column', 'shared_at')

admin.site.register(SharedDocument, SharedDocumentAdmin)
