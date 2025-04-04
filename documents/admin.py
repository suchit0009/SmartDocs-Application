from django.contrib import admin
from .models import Document, DocumentInformation, ChatMessage

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('title', 'category', 'uploaded_by__username')
    list_filter = ('category', 'file_type')

@admin.register(DocumentInformation)
class DocumentInformationAdmin(admin.ModelAdmin):
    search_fields = ('document__title', 'extracted_info')  # Search by document title and extracted info
    list_filter = ('document__category',)  # Filter by document category

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'question', 'answer', 'timestamp')
    search_fields = ('user__username', 'document__title', 'question', 'answer')
    list_filter = ('timestamp', 'user', 'document')
    date_hierarchy = 'timestamp'  # Optional: adds a date-based navigation