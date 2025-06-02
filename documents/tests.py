import pytest
import json
import os
import tempfile
from unittest.mock import patch
from django.test import Client
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.http import Http404, FileResponse
from django.conf import settings
from documents.models import Document, DocumentInformation, ChatMessage
from documents.forms import DocumentUploadForm
from documents.views import (
    upload_document, document_list, document_detail, edit_document,
    download_document, fetch_document_data, update_document_data,
    check_shared_status, ask_document_question, run_information_extraction
)
from sharing.models import SharedDocument
from PIL import Image

# Get the custom user model
User = get_user_model()

# Fixtures
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )

@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='otheruser',
        email='otheruser@example.com',
        password='testpass123'
    )

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def auth_client(client, user):
    client.login(username='testuser', password='testpass123')
    return client

@pytest.fixture
def image_file():
    """Fixture to load an image from a custom path."""
    custom_image_path = '/Users/suchit/Desktop/YEAR 3/FYP/SmartDocs-Application copy/SmartDocs/media/documents/aaditya.jpeg'
    if not os.path.exists(custom_image_path):
        pytest.fail(f"Custom image not found at {custom_image_path}. Please add a test_image.png to {os.path.join(settings.MEDIA_ROOT, 'documents')}.")
    
    with open(custom_image_path, 'rb') as f:
        file_content = f.read()
    
    # Create UploadedFile for testing
    uploaded_file = UploadedFile(
        file=open(custom_image_path, 'rb'),
        name='test_image.png',
        content_type='image/png',
        size=len(file_content)
    )
    yield uploaded_file
    uploaded_file.close()

@pytest.fixture
def document(user, image_file):
    doc = Document.objects.create(
        title='Test Document',
        file=image_file,
        file_type='.png',
        file_size=image_file.size,
        category='Invoice',
        uploaded_by=user
    )
    image_file.close()
    return doc

@pytest.fixture
def shared_document(user, other_user, image_file):
    doc = Document.objects.create(
        title='Shared Document',
        file=image_file,
        file_type='.png',
        file_size=image_file.size,
        category='Invoice',
        uploaded_by=user
    )
    SharedDocument.objects.create(
        document=doc,
        shared_with=other_user,
        shared_by=user,
        permission='edit'
    )
    image_file.close()
    return doc

# ------------------- Model Tests -------------------
@pytest.mark.django_db
def test_document_creation(user, image_file):
    doc = Document.objects.create(
        title='Test Doc',
        file=image_file,
        file_type='.png',
        file_size=image_file.size,
        category='Invoice',
        uploaded_by=user
    )
    image_file.close()
    assert doc.title == 'Test Doc'
    assert doc.file_type == '.png'
    assert doc.file_size == image_file.size
    assert doc.category == 'Invoice'
    assert doc.uploaded_by == user
    assert doc.uploaded_at is not None

@pytest.mark.django_db
def test_document_default_title(user, image_file):
    doc = Document.objects.create(
        file=image_file,
        uploaded_by=user
    )
    image_file.close()
    assert doc.title == 'Untitled Document'

@pytest.mark.django_db
def test_document_auto_file_size(user, image_file):
    doc = Document(
        file=image_file,
        uploaded_by=user
    )
    doc.save()
    image_file.close()
    assert doc.file_size == image_file.size

@pytest.mark.django_db
def test_document_str(user, image_file):
    doc = Document.objects.create(
        title='Test Doc',
        file=image_file,
        uploaded_by=user
    )
    image_file.close()
    assert str(doc) == 'Test Doc'

@pytest.mark.django_db
def test_document_str_no_title(user, image_file):
    doc = Document.objects.create(
        file=image_file,
        uploaded_by=user
    )
    image_file.close()
    assert str(doc) == 'Untitled Document'

@pytest.mark.django_db
def test_document_information_creation(document):
    doc_info = DocumentInformation.objects.create(
        document=document,
        extracted_info={'key': 'value'}
    )
    assert doc_info.document == document
    assert doc_info.extracted_info == {'key': 'value'}
    assert str(doc_info) == f"Information for {document.title}"

@pytest.mark.django_db
def test_chat_message_creation(user, document):
    chat = ChatMessage.objects.create(
        user=user,
        document=document,
        question='What is this?',
        answer='This is a test.'
    )
    assert chat.user == user
    assert chat.document == document
    assert chat.question == 'What is this?'
    assert chat.answer == 'This is a test.'
    assert chat.timestamp is not None
    assert str(chat) == f"{user.username} - {chat.question} - {chat.timestamp}"

@pytest.mark.django_db
def test_chat_message_ordering(user, document):
    chat1 = ChatMessage.objects.create(
        user=user, document=document, question='Q1', answer='A1'
    )
    chat2 = ChatMessage.objects.create(
        user=user, document=document, question='Q2', answer='A2'
    )
    chats = ChatMessage.objects.all()
    assert chats[0] == chat1
    assert chats[1] == chat2

# ------------------- Form Tests -------------------
@pytest.mark.django_db
def test_document_upload_form_valid(image_file):
    form_data = {}
    files = {'file': image_file}
    form = DocumentUploadForm(data=form_data, files=files)
    assert form.is_valid()
    doc = form.save(commit=False)
    assert doc.file == image_file
    image_file.close()

@pytest.mark.django_db
def test_document_upload_form_no_file():
    form = DocumentUploadForm(data={}, files={})
    assert not form.is_valid()
    assert 'file' in form.errors

# ------------------- View Tests -------------------
@pytest.mark.django_db
@patch('documents.views.classify_document', return_value='Invoice')
@patch('documents.views.run_information_extraction', return_value={'key': 'value'})
def test_upload_document_post_valid(mock_extract, mock_classify, auth_client, user, image_file):
    response = auth_client.post(
        reverse('documents:upload'),
        {'document': image_file},  # Changed to 'document' to match view
        format='multipart'
    )
    image_file.close()
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    assert response.json()['status'] == 'success'
    doc = Document.objects.get(uploaded_by=user)
    assert doc.title == os.path.splitext(image_file.name)[0]
    assert doc.file_type == '.png'
    assert doc.file_size == image_file.size
    assert doc.category == 'Invoice'
    doc_info = DocumentInformation.objects.get(document=doc)
    assert isinstance(doc_info.extracted_info, dict)
    assert doc_info.extracted_info == {'key': 'value'}

@pytest.mark.django_db
def test_upload_document_post_extraction_failure(auth_client, image_file):
    original_extract = run_information_extraction
    def failing_extract(*args, **kwargs):
        raise Exception('Extraction failed')
    try:
        from documents import views
        views.run_information_extraction = failing_extract
        with patch('documents.views.classify_document', return_value='Invoice'):
            response = auth_client.post(
                reverse('documents:upload'),
                {'document': image_file},  # Changed to 'document' to match view
                format='multipart'
            )
        image_file.close()
        assert response.status_code == 400
        assert response.json()['status'] == 'error'
        assert 'information extraction failed' in response.json()['message']
        doc = Document.objects.get()
        doc_info = DocumentInformation.objects.get(document=doc)
        assert doc_info.extracted_info['error'] == 'Could not extract invoice information'
    finally:
        views.run_information_extraction = original_extract

@pytest.mark.django_db
def test_upload_document_post_no_file(auth_client):
    response = auth_client.post(reverse('documents:upload'), {})
    assert response.status_code == 400
    assert response.json()['status'] == 'error'
    assert response.json()['message'] == 'No file uploaded'

@pytest.mark.django_db
def test_upload_document_unauthenticated(client):
    response = client.post(reverse('documents:upload'), {})
    assert response.status_code == 302
    assert response.url.startswith('/login/')

@pytest.mark.django_db
def test_document_list_authenticated(auth_client, document):
    response = auth_client.get(reverse('documents:document_list'))
    assert response.status_code == 200
    assert 'documents/document_list.html' in [t.name for t in response.templates]
    assert document in response.context['documents']

@pytest.mark.django_db
def test_document_list_unauthenticated(client):
    response = client.get(reverse('documents:document_list'))
    assert response.status_code == 302
    assert response.url.startswith('/login/')

@pytest.mark.django_db
def test_document_detail_owner(auth_client, document):
    response = auth_client.get(reverse('documents:document_detail', args=[document.id]))
    assert response.status_code == 200
    assert 'documents/document_detail.html' in [t.name for t in response.templates]
    assert response.context['document'] == document
    assert response.context['has_edit_permission'] is True

@pytest.mark.django_db
def test_document_detail_shared_with_edit(shared_document, client, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:document_detail', args=[shared_document.id]))
    assert response.status_code == 200
    assert response.context['document'] == shared_document
    assert response.context['has_edit_permission'] is True

@pytest.mark.django_db
def test_document_detail_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:document_detail', args=[document.id]))
    assert response.status_code == 404

@pytest.mark.django_db
def test_document_detail_unauthenticated(client, document):
    response = client.get(reverse('documents:document_detail', args=[document.id]))
    assert response.status_code == 302
    assert response.url.startswith('/login/')

@pytest.mark.django_db
def test_edit_document_get(auth_client, document):
    response = auth_client.get(reverse('documents:edit_document', args=[document.id]))
    assert response.status_code == 200
    assert 'documents/edit_document.html' in [t.name for t in response.templates]
    assert response.context['document'] == document

@pytest.mark.django_db
def test_edit_document_post_valid(auth_client, document):
    response = auth_client.post(reverse('documents:edit_document', args=[document.id]), {
        'title': 'Updated Title',
        'category': 'License'
    })
    assert response.status_code == 302
    assert response.url == reverse('home')
    document.refresh_from_db()
    assert document.title == 'Updated Title'
    assert document.category == 'License'

@pytest.mark.django_db
def test_edit_document_post_shared(auth_client, shared_document):
    response = auth_client.post(reverse('documents:edit_document', args=[shared_document.id]), {
        'title': 'Updated Title',
        'category': 'License'
    })
    assert response.status_code == 302
    assert response.url == reverse('home')
    shared_document.refresh_from_db()
    assert shared_document.title != 'Updated Title'  # Should not update
    assert shared_document.category != 'License'

@pytest.mark.django_db
def test_edit_document_unauthorized(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:edit_document', args=[document.id]))
    assert response.status_code == 404

@pytest.mark.django_db
def test_download_document_owner(auth_client, document):
    response = auth_client.get(reverse('documents:download_document', args=[document.id]))
    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.get('Content-Disposition') == f'attachment; filename="{document.title}"'

@pytest.mark.django_db
def test_download_document_shared(shared_document, client, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:download_document', args=[shared_document.id]))
    assert isinstance(response, FileResponse)
    assert response.status_code == 200

@pytest.mark.django_db
def test_download_document_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:download_document', args=[document.id]))
    assert response.status_code == 404

@pytest.mark.django_db
def test_download_document_file_missing(auth_client, document):
    document.file = None
    document.save()
    response = auth_client.get(reverse('documents:download_document', args=[document.id]))
    assert response.status_code == 404
    assert response.json()['error'] == 'No file associated with this document'

@pytest.mark.django_db
def test_fetch_document_data_owner(auth_client, document):
    doc_info = DocumentInformation.objects.create(
        document=document,
        extracted_info={'key': 'value'}
    )
    response = auth_client.get(reverse('documents:fetch_document_data', args=[document.id]))
    assert response.status_code == 200
    assert response.json() == {'key': 'value'}

@pytest.mark.django_db
def test_fetch_document_data_shared(shared_document, client, other_user):
    doc_info = DocumentInformation.objects.create(
        document=shared_document,
        extracted_info={'key': 'value'}
    )
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:fetch_document_data', args=[shared_document.id]))
    assert response.status_code == 200
    assert response.json() == {'key': 'value'}

@pytest.mark.django_db
def test_fetch_document_data_no_info(auth_client, document):
    response = auth_client.get(reverse('documents:fetch_document_data', args=[document.id]))
    assert response.status_code == 404
    assert response.json()['error'] == 'Document exists but no extracted data found'

@pytest.mark.django_db
def test_fetch_document_data_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:fetch_document_data', args=[document.id]))
    assert response.status_code == 403

@pytest.mark.django_db
def test_update_document_data_valid(auth_client, document):
    doc_info = DocumentInformation.objects.create(
        document=document,
        extracted_info={'key': 'value'}
    )
    updated_data = {'new_key': 'new_value'}
    response = auth_client.post(
        reverse('documents:update_document_data', args=[document.id]),
        json.dumps(updated_data),
        content_type='application/json'
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
    doc_info.refresh_from_db()
    assert doc_info.extracted_info == updated_data

@pytest.mark.django_db
def test_update_document_data_shared_edit(shared_document, client, other_user):
    doc_info = DocumentInformation.objects.create(
        document=shared_document,
        extracted_info={'key': 'value'}
    )
    updated_data = {'new_key': 'new_value'}
    client.login(username='otheruser', password='testpass123')
    response = client.post(
        reverse('documents:update_document_data', args=[shared_document.id]),
        json.dumps(updated_data),
        content_type='application/json'
    )
    assert response.status_code == 200
    doc_info.refresh_from_db()
    assert doc_info.extracted_info == updated_data

@pytest.mark.django_db
def test_update_document_data_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.post(
        reverse('documents:update_document_data', args=[document.id]),
        json.dumps({'key': 'value'}),
        content_type='application/json'
    )
    assert response.status_code == 403

@pytest.mark.django_db
def test_update_document_data_invalid_method(auth_client, document):
    response = auth_client.get(reverse('documents:update_document_data', args=[document.id]))
    assert response.status_code == 405
    assert response.json()['error'] == 'Invalid request method'

@pytest.mark.django_db
def test_check_shared_status_not_shared(auth_client, document):
    response = auth_client.get(reverse('documents:check_shared_status', args=[document.id]))
    assert response.status_code == 200
    assert response.json()['is_shared'] is False

@pytest.mark.django_db
def test_check_shared_status_shared(auth_client, shared_document, other_user):
    response = auth_client.get(reverse('documents:check_shared_status', args=[shared_document.id]))
    assert response.status_code == 200
    assert response.json()['is_shared'] is True
    assert response.json()['shared_with_count'] == 1
    assert response.json()['shared_with_usernames'] == 'otheruser'

@pytest.mark.django_db
def test_check_shared_status_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.get(reverse('documents:check_shared_status', args=[document.id]))
    assert response.status_code == 404

@pytest.mark.django_db
@patch('documents.views.run_docvqa', return_value='Sample answer')
def test_ask_document_question_valid(mock_docvqa, auth_client, document):
    question = {'question': 'What is this?'}
    response = auth_client.post(
        reverse('documents:ask_document_question', args=[document.id]),
        json.dumps(question),
        content_type='application/json'
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    assert 'answer' in response.json()
    assert response.json()['answer'] == 'Sample answer'
    chat = ChatMessage.objects.get(document=document)
    assert chat.question == 'What is this?'
    assert chat.answer == 'Sample answer'
    assert chat.user == document.uploaded_by

@pytest.mark.django_db
def test_ask_document_question_no_question(auth_client, document):
    response = auth_client.post(
        reverse('documents:ask_document_question', args=[document.id]),
        json.dumps({'question': ''}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'No question provided'

@pytest.mark.django_db
def test_ask_document_question_invalid_json(auth_client, document):
    response = auth_client.post(
        reverse('documents:ask_document_question', args=[document.id]),
        'invalid json',
        content_type='application/json'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid JSON data'

@pytest.mark.django_db
def test_ask_document_question_no_access(client, document, other_user):
    client.login(username='otheruser', password='testpass123')
    response = client.post(
        reverse('documents:ask_document_question', args=[document.id]),
        json.dumps({'question': 'What?'}),
        content_type='application/json'
    )
    assert response.status_code == 403
