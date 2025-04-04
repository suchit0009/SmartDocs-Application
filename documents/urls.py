from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import edit_document

app_name = 'documents'

urlpatterns = [
    path('upload/', views.upload_document, name='upload'),
    path('list/', views.document_list, name='document_list'),
    path('view/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('edit/<int:doc_id>/', edit_document, name='edit_document'),
    path('document/<int:doc_id>/data/', views.fetch_document_data, name='fetch_document_data'),
    path('document/<int:doc_id>/update/', views.update_document_data, name='update_document_data'),
    path('check-shared-status/<int:doc_id>/', views.check_shared_status, name='check_shared_status'),
    path('download/<int:doc_id>/', views.download_document, name='download_document'),
    path('documents/document/<int:doc_id>/ask/', views.ask_document_question, name='ask_document_question'),
]

