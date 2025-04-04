# documents/models.py
from django.db import models
from django.conf import settings

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('License', 'License'),
        ('Passport', 'Passport'),
        ('Invoice', 'Invoice'),
        ('Check', 'Check'),
        ('Resume', 'Resume'),
    ]

    title = models.CharField(max_length=255, null=True, blank=True, default='Untitled Document')
    file = models.FileField(upload_to='documents/') 
    file_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='OTHER')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    s3_key = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return self.title or 'Untitled Document'
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size  # Populate file_size in bytes
        super().save(*args, **kwargs)


class DocumentInformation(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='information')  # ForeignKey to the Document model's id
    extracted_info = models.JSONField()  # This will store the extracted JSON data

    def __str__(self):
        return f"Information for {self.document.title or 'Untitled Document'}"
    
# documents/models.py
from django.db import models
from accounts.models import CustomUser  # Import your custom user model

class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Reference CustomUser
    document = models.ForeignKey('Document', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.question} - {self.timestamp}"
