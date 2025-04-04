from django.db import models
from documents.models import Document
from django.conf import settings

class SharedDocument(models.Model):
    PERMISSION_CHOICES = (
        ('view', 'View Only'),
        ('edit', 'Edit')
    )
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shared_with')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='shared_documents', on_delete=models.CASCADE)
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_documents', on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    shared_at = models.DateTimeField(auto_now_add=True)

    def get_permission_display(self):
        return dict(self.PERMISSION_CHOICES).get(self.permission, self.permission)

    class Meta:
        unique_together = ('document', 'shared_with')
        
    def __str__(self):
        return f"{self.document} shared with {self.shared_with.username} ({self.permission})"