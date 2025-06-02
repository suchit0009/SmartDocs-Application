import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import Client
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from documents.models import Document
from sharing.models import SharedDocument
from datetime import datetime

User = get_user_model()

# Fixtures
@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    assert user.id is not None, "User ID is not set"
    return user

@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='otheruser',
        email='otheruser@example.com',
        password='testpass123'
    )

@pytest.fixture
def third_user(db):
    return User.objects.create_user(
        username='thirduser',
        email='thirduser@example.com',
        password='testpass123'
    )

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def auth_client(client, user):
    client.force_login(user)  # Use force_login to ensure authentication
    session = client.session
    session['_auth_user_id'] = str(user.pk)  # Explicitly set user ID
    session.save()
    assert session['_auth_user_id'] == str(user.pk), "Session user ID not set"
    return client

@pytest.fixture
def image_file():
    """Stubbed UploadedFile to avoid file system dependency."""
    mock_file = MagicMock(spec=UploadedFile)
    mock_file.name = 'test_image.png'
    mock_file.content_type = 'image/png'
    mock_file.size = 1024
    mock_file.close = MagicMock()
    return mock_file

@pytest.fixture
def document(user, image_file):
    """Stub Document creation and retrieval."""
    with patch('documents.models.Document.objects.create') as mock_create, \
         patch('django.shortcuts.get_object_or_404') as mock_get:
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.title = 'Test Document'
        mock_doc.file = image_file
        mock_doc.file_type = '.png'
        mock_doc.file_size = image_file.size
        mock_doc.category = 'Invoice'
        mock_doc.uploaded_by = user
        mock_create.return_value = mock_doc
        mock_get.return_value = mock_doc
        doc = Document.objects.create(
            title='Test Document',
            file=image_file,
            file_type='.png',
            file_size=image_file.size,
            category='Invoice',
            uploaded_by=user
        )
        return doc

# ------------------- Model Tests -------------------
@pytest.mark.django_db
def test_shared_document_creation(document, user, other_user):
    """Mock SharedDocument creation to verify attributes."""
    with patch('sharing.models.SharedDocument.objects.create') as mock_create:
        mock_shared_doc = MagicMock(spec=SharedDocument)
        mock_shared_doc.document = document
        mock_shared_doc.shared_by = user
        mock_shared_doc.shared_with = other_user
        mock_shared_doc.permission = 'view'
        mock_shared_doc.shared_at = datetime.now()
        mock_shared_doc.__str__.return_value = f"{document} shared with {other_user.username} (view)"
        mock_create.return_value = mock_shared_doc

        shared_doc = SharedDocument.objects.create(
            document=document,
            shared_by=user,
            shared_with=other_user,
            permission='view'
        )
        assert shared_doc.document == document
        assert shared_doc.shared_by == user
        assert shared_doc.shared_with == other_user
        assert shared_doc.permission == 'view'
        assert shared_doc.shared_at is not None
        assert str(shared_doc) == f"{document} shared with {other_user.username} (view)"
        mock_create.assert_called_once()

@pytest.mark.django_db
def test_shared_document_unique_together(document, user, other_user):
    """Mock SharedDocument creation to test unique_together constraint."""
    with patch('sharing.models.SharedDocument.objects.create') as mock_create:
        mock_create.side_effect = [None, Exception("IntegrityError")]
        SharedDocument.objects.create(
            document=document,
            shared_by=user,
            shared_with=other_user,
            permission='view'
        )
        with pytest.raises(Exception):
            SharedDocument.objects.create(
                document=document,
                shared_by=user,
                shared_with=other_user,
                permission='edit'
            )
        assert mock_create.call_count == 2

@pytest.mark.django_db
def test_shared_document_get_permission_display(document, user, other_user):
    """Mock SharedDocument to test get_permission_display."""
    with patch('sharing.models.SharedDocument.objects.create') as mock_create:
        mock_shared_doc = MagicMock(spec=SharedDocument)
        mock_shared_doc.get_permission_display.return_value = 'Edit'
        mock_create.return_value = mock_shared_doc
        shared_doc = SharedDocument.objects.create(
            document=document,
            shared_by=user,
            shared_with=other_user,
            permission='edit'
        )
        assert shared_doc.get_permission_display() == 'Edit'
        mock_create.assert_called_once()

# ------------------- View Tests -------------------
@pytest.mark.django_db
def test_share_document_valid(auth_client, document, other_user, third_user):
    """Mock User.objects, SharedDocument.objects, and logger."""
    with patch('django.contrib.auth.get_user_model') as mock_user_model, \
         patch('sharing.models.SharedDocument.objects.update_or_create') as mock_update, \
         patch('sharing.views.logger') as mock_logger:
        mock_user_model.return_value.objects.filter.return_value = [other_user, third_user]
        mock_update.side_effect = [(MagicMock(), True), (MagicMock(), True)]
        
        data = {
            'users': [other_user.id, third_user.id],
            'permission': 'view'
        }
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()['success'] is True
        assert len(response.json()['results']) == 2
        assert response.json()['results'][0]['user_id'] == other_user.id
        assert response.json()['results'][0]['status'] == 'created'
        assert response.json()['results'][0]['permission'] == 'view'
        assert response.json()['results'][1]['user_id'] == third_user.id
        assert response.json()['results'][1]['status'] == 'created'
        assert response.json()['results'][1]['permission'] == 'view'
        mock_update.assert_called()
        mock_logger.debug.assert_any_call(f"Attempting to share document with ID: {document.id}")

@pytest.mark.django_db
def test_share_document_update_existing(auth_client, document, other_user):
    """Mock existing SharedDocument and update behavior."""
    with patch('sharing.models.SharedDocument.objects.create') as mock_create, \
         patch('sharing.models.SharedDocument.objects.update_or_create') as mock_update, \
         patch('sharing.views.logger') as mock_logger:
        mock_create.return_value = MagicMock()
        mock_update.return_value = (MagicMock(permission='edit'), False)
        
        SharedDocument.objects.create(
            document=document,
            shared_by=document.uploaded_by,
            shared_with=other_user,
            permission='view'
        )
        data = {
            'users': [other_user.id],
            'permission': 'edit'
        }
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()['success'] is True
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['user_id'] == other_user.id
        assert response.json()['results'][0]['status'] == 'updated'
        assert response.json()['results'][0]['permission'] == 'edit'
        mock_update.assert_called()
        mock_logger.debug.assert_called()

@pytest.mark.django_db
def test_share_document_invalid_permission(auth_client, document, other_user):
    """Mock logger for error logging."""
    with patch('sharing.views.logger') as mock_logger:
        data = {
            'users': [other_user.id],
            'permission': 'invalid'
        }
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.json()['error'] == 'Invalid permission. Allowed values are "view" and "edit".'
        mock_logger.debug.assert_any_call(f"Attempting to share document with ID: {document.id}")

@pytest.mark.django_db
def test_share_document_empty_user_list(auth_client, document):
    """Mock logger for error logging."""
    with patch('sharing.views.logger') as mock_logger:
        data = {
            'users': [],
            'permission': 'view'
        }
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.json()['error'] == 'User list cannot be empty'
        mock_logger.debug.assert_any_call(f"Attempting to share document with ID: {document.id}")

@pytest.mark.django_db
def test_share_document_invalid_user(auth_client, document):
    """Mock User.objects to return empty queryset."""
    with patch('django.contrib.auth.get_user_model') as mock_user_model, \
         patch('sharing.views.logger') as mock_logger:
        mock_user_model.return_value.objects.filter.return_value = []
        data = {
            'users': [999],
            'permission': 'view'
        }
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()['success'] is True
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['user_id'] == 999
        assert response.json()['results'][0]['status'] == 'error'
        assert response.json()['results'][0]['message'] == 'User not found'
        mock_logger.debug.assert_any_call(f"Attempting to share document with ID: {document.id}")

@pytest.mark.django_db
def test_share_document_unauthenticated(client, document):
    """No mocks needed; tests redirect behavior."""
    data = {
        'users': [1],
        'permission': 'view'
    }
    response = client.post(
        reverse('sharing:share_document', args=[document.id]),
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert response.url.startswith('/login/')

@pytest.mark.django_db
def test_share_document_not_owner(auth_client, document, other_user):
    """Tests permission logic by logging in as a non-owner."""
    client = Client()
    client.force_login(other_user)
    data = {
        'users': [1],
        'permission': 'view'
    }
    response = client.post(
        reverse('sharing:share_document', args=[document.id]),
        json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

@pytest.mark.django_db
def test_share_document_invalid_json(auth_client, document):
    """Mock json.loads to simulate JSON error."""
    with patch('json.loads') as mock_json_loads, \
         patch('sharing.views.logger') as mock_logger:
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response = auth_client.post(
            reverse('sharing:share_document', args=[document.id]),
            'invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.json()['error'] == 'Invalid JSON format'
        mock_json_loads.assert_called_once_with('invalid json')
        mock_logger.debug.assert_any_call(f"Attempting to share document with ID: {document.id}")

@pytest.mark.django_db
def test_shared_documents(auth_client, document, other_user):
    """Mock SharedDocument.objects to simulate query."""
    with patch('sharing.models.SharedDocument.objects.filter') as mock_filter:
        mock_shared_doc = MagicMock()
        mock_shared_doc.document.id = document.id
        mock_shared_doc.document.title = document.title
        mock_shared_doc.document.category = document.category
        mock_shared_doc.shared_by.username = document.uploaded_by.username
        mock_shared_doc.permission = 'view'
        mock_shared_doc.shared_at = datetime.now()
        mock_shared_doc.shared_at.strftime.return_value = '2025-04-28 12:00:00'
        mock_filter.return_value.select_related.return_value = [mock_shared_doc]
        
        client = Client()
        client.force_login(other_user)
        response = client.get(reverse('sharing:shared_documents'))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()['success'] is True
        assert len(response.json()['documents']) == 1
        doc_data = response.json()['documents'][0]
        assert doc_data['id'] == document.id
        assert doc_data['title'] == document.title
        assert doc_data['category'] == document.category
        assert doc_data['shared_by'] == document.uploaded_by.username
        assert doc_data['permission'] == 'view'
        mock_filter.assert_called()

@pytest.mark.django_db
def test_shared_documents_none(auth_client):
    """Mock SharedDocument.objects to return empty queryset."""
    with patch('sharing.models.SharedDocument.objects.filter') as mock_filter:
        mock_filter.return_value.select_related.return_value = []
        response = auth_client.get(reverse('sharing:shared_documents'))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()['success'] is True
        assert len(response.json()['documents']) == 0
        mock_filter.assert_called()

@pytest.mark.django_db
def test_shared_documents_unauthenticated(client):
    """No mocks needed; tests redirect behavior."""
    response = client.get(reverse('sharing:shared_documents'))
    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert response.url.startswith('/login/')

@pytest.mark.django_db
def test_share_document_url():
    url = reverse('sharing:share_document', args=[1])
    assert url == '/sharing/api/share/1/'

@pytest.mark.django_db
def test_get_users_url():
    url = reverse('sharing:get_users')
    assert url == '/sharing/api/users/'

@pytest.mark.django_db
def test_shared_documents_url():
    url = reverse('sharing:shared_documents')
    assert url == '/sharing/api/shared-documents/'