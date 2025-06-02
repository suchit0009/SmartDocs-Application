from django.urls import path
from .views import share_document, shared_documents
from accounts.views import user_list_api 

app_name = "sharing"

urlpatterns = [
    path('api/users/', user_list_api, name='get_users'),
    path('api/share/<int:document_id>/', share_document, name='share_document'),
    path('api/shared-documents/', shared_documents, name='shared_documents'),
]

