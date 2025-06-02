import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse, resolve
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from accounts.forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordChangeForm, ProfileUpdateForm
from accounts.models import CustomUser
from accounts.utils import handle_login_errors
from accounts.views import login_view, register_view, home, user_list_api, change_password, update_profile, landing
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from unittest.mock import patch
import datetime

# Get the custom user model
User = get_user_model()

# Fixture for authenticated user
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )

# Fixture for anonymous client
@pytest.fixture
def client():
    return Client()

# Fixture for authenticated client
@pytest.fixture
def auth_client(client, user):
    client.login(username='testuser', password='testpass123')
    return client

# ------------------- Model Tests -------------------
@pytest.mark.django_db
def test_custom_user_creation():
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        birthday=datetime.date(1990, 1, 1),
        phone_number='1234567890'
    )
    assert user.username == 'testuser'
    assert user.email == 'testuser@example.com'
    assert user.check_password('testpass123')
    assert user.birthday == datetime.date(1990, 1, 1)
    assert user.phone_number == '1234567890'
    assert not user.profile_picture  # Handles ImageFieldFile

@pytest.mark.django_db
def test_custom_user_str():
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    print(f"User string representation: {str(user)}")
    assert str(user) == 'testuser'

@pytest.mark.django_db
def test_custom_user_unique_email():
    User.objects.create_user(
        username='user1',
        email='test@example.com',
        password='testpass123'
    )
    with pytest.raises(Exception):  # Should raise IntegrityError
        User.objects.create_user(
            username='user2',
            email='test@example.com',
            password='testpass123'
        )

@pytest.mark.django_db
def test_custom_user_nullable_fields():
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    assert not user.profile_picture  # Handles ImageFieldFile
    assert user.birthday is None
    assert user.phone_number is None

# ------------------- Form Tests -------------------
@pytest.mark.django_db
def test_custom_user_creation_form_valid():
    form_data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    form = CustomUserCreationForm(data=form_data)
    assert form.is_valid()
    user = form.save()
    assert user.username == 'newuser'
    assert user.email == 'newuser@example.com'
    assert user.check_password('testpass123')

@pytest.mark.django_db
def test_custom_user_creation_form_invalid_email():
    form_data = {
        'username': 'newuser',
        'email': 'invalid-email',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'email' in form.errors

@pytest.mark.django_db
def test_custom_user_creation_form_mismatched_passwords():
    form_data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password1': 'testpass123',
        'password2': 'differentpass'
    }
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'password2' in form.errors

@pytest.mark.django_db
def test_custom_user_creation_form_duplicate_email():
    User.objects.create_user(
        username='existinguser',
        email='test@example.com',
        password='testpass123'
    )
    form_data = {
        'username': 'newuser',
        'email': 'test@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'email' in form.errors

@pytest.mark.django_db
def test_custom_authentication_form_valid():
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    form_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    form = CustomAuthenticationForm(data=form_data)
    assert form.is_valid()

@pytest.mark.django_db
def test_custom_authentication_form_invalid_credentials():
    User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    form_data = {
        'username': 'testuser',
        'password': 'wrongpass'
    }
    form = CustomAuthenticationForm(data=form_data)
    assert not form.is_valid()
    assert '__all__' in form.errors

@pytest.mark.django_db
def test_custom_password_change_form_valid(user):
    form_data = {
        'old_password': 'testpass123',
        'new_password1': 'newpass123',
        'new_password2': 'newpass123'
    }
    form = CustomPasswordChangeForm(user=user, data=form_data)
    assert form.is_valid()
    form.save()
    assert user.check_password('newpass123')

@pytest.mark.django_db
def test_custom_password_change_form_invalid_old_password(user):
    form_data = {
        'old_password': 'wrongpass',
        'new_password1': 'newpass123',
        'new_password2': 'newpass123'
    }
    form = CustomPasswordChangeForm(user=user, data=form_data)
    assert not form.is_valid()
    assert 'old_password' in form.errors

@pytest.mark.django_db
def test_custom_password_change_form_mismatched_passwords(user):
    form_data = {
        'old_password': 'testpass123',
        'new_password1': 'newpass123',
        'new_password2': 'differentpass'
    }
    form = CustomPasswordChangeForm(user=user, data=form_data)
    assert not form.is_valid()
    assert 'new_password2' in form.errors

@pytest.mark.django_db
def test_profile_update_form_valid(user):
    form_data = {
        'username': 'updateduser',
        'email': 'updated@example.com',
        'phone_number': '1234567890',
        'birthday': '1990-01-01'
    }
    form = ProfileUpdateForm(data=form_data, instance=user)
    assert form.is_valid()
    updated_user = form.save()
    assert updated_user.username == 'updateduser'
    assert updated_user.email == 'updated@example.com'
    assert updated_user.phone_number == '1234567890'
    assert updated_user.birthday == datetime.date(1990, 1, 1)

@pytest.mark.django_db
def test_profile_update_form_invalid_email(user):
    form_data = {
        'username': 'updateduser',
        'email': 'invalid-email',
        'phone_number': '1234567890',
        'birthday': '1990-01-01'
    }
    form = ProfileUpdateForm(data=form_data, instance=user)
    assert not form.is_valid()
    assert 'email' in form.errors

@pytest.mark.django_db
def test_profile_update_form_with_image(user):
    with open('/Users/suchit/Desktop/YEAR 3/FYP/SmartDocs-Application copy/SmartDocs/media/profile_pics/dog_swap_MbWI3dV.jpg', 'rb') as img_file:
        image = SimpleUploadedFile("profile.jpg", img_file.read(), content_type="image/jpeg")
    form_data = {
        'username': 'updateduser',
        'email': 'updated@example.com',
        'phone_number': '1234567890',
        'birthday': '1990-01-01'
    }
    files = {'profile_picture': image}
    form = ProfileUpdateForm(data=form_data, files=files, instance=user)
    assert form.is_valid(), form.errors
    updated_user = form.save()
    assert updated_user.profile_picture
    assert 'profile_pics' in updated_user.profile_picture.path

# ------------------- Utils Tests -------------------
@pytest.mark.django_db
@patch('django.contrib.messages.error')
def test_handle_login_errors_no_username_no_password(mock_messages, rf):
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={})
    result = handle_login_errors(request, form, '', '')
    assert result is False
    mock_messages.assert_called_with(request, "Please enter both username and password")

@pytest.mark.django_db
@patch('django.contrib.messages.error')
def test_handle_login_errors_no_username(mock_messages, rf):
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={})
    result = handle_login_errors(request, form, '', 'testpass123')
    assert result is False
    mock_messages.assert_called_with(request, "Username is required")

@pytest.mark.django_db
@patch('django.contrib.messages.error')
def test_handle_login_errors_no_password(mock_messages, rf):
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={})
    result = handle_login_errors(request, form, 'testuser', '')
    assert result is False
    mock_messages.assert_called_with(request, "Password is required")

@pytest.mark.django_db
@patch('django.contrib.messages.error')
def test_handle_login_errors_invalid_credentials(mock_messages, rf):
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={})
    result = handle_login_errors(request, form, 'testuser', 'wrongpass')
    assert result is False
    mock_messages.assert_called_with(request, "Invalid username or password")

@pytest.mark.django_db
@patch('django.contrib.messages.error')
def test_handle_login_errors_inactive_user(mock_messages, rf):
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        is_active=False
    )
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={})
    result = handle_login_errors(request, form, 'testuser', 'testpass123')
    assert result is False
    mock_messages.assert_called_with(request, "Invalid username or password")

@pytest.mark.django_db
def test_handle_login_errors_valid_credentials(rf, user):
    request = rf.post('/login/')
    form = CustomAuthenticationForm(data={'username': 'testuser', 'password': 'testpass123'})
    result = handle_login_errors(request, form, 'testuser', 'testpass123')
    assert result is True

# ------------------- View Tests -------------------
@pytest.mark.django_db
def test_landing_view(client):
    response = client.get(reverse('landing'))
    assert response.status_code == 200
    assert 'accounts/landing.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_login_view_get(client):
    response = client.get(reverse('login'))
    assert response.status_code == 200
    assert 'accounts/login.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form'], AuthenticationForm)

@pytest.mark.django_db
def test_login_view_post_valid(client, user):
    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 302
    assert response.url == reverse('home')
    assert client.session.get('_auth_user_id')

@pytest.mark.django_db
def test_login_view_post_invalid(client):
    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'wrongpass'
    })
    assert response.status_code == 200
    assert 'accounts/login.html' in [t.name for t in response.templates]
    assert 'form' in response.context
    assert not response.context['form'].is_valid()

@pytest.mark.django_db
def test_register_view_get(client):
    response = client.get(reverse('register'))
    assert response.status_code == 200
    assert 'accounts/register.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form'], CustomUserCreationForm)

@pytest.mark.django_db
def test_register_view_post_valid(client):
    response = client.post(reverse('register'), {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123'
    })
    assert response.status_code == 302
    assert response.url == reverse('login')
    assert User.objects.filter(username='newuser').exists()

@pytest.mark.django_db
def test_register_view_post_invalid(client):
    response = client.post(reverse('register'), {
        'username': 'newuser',
        'email': 'invalid-email',
        'password1': 'testpass123',
        'password2': 'testpass123'
    })
    assert response.status_code == 200
    assert 'accounts/register.html' in [t.name for t in response.templates]
    assert 'form' in response.context
    assert not response.context['form'].is_valid()

@pytest.mark.django_db
def test_home_view_unauthenticated(client):
    response = client.get(reverse('home'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('login'))

@pytest.mark.django_db
def test_home_view_authenticated(auth_client, user):
    response = auth_client.get(reverse('home'))
    assert response.status_code == 200
    assert 'accounts/home.html' in [t.name for t in response.templates]
    assert 'latest_documents' in response.context
    assert 'total_documents' in response.context

@pytest.mark.django_db
def test_user_list_api(client, user):
    response = client.get(reverse('user_list_api'))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['username'] == 'testuser'
    assert data[0]['email'] == 'testuser@example.com'

@pytest.mark.django_db
def test_change_password_view_get(auth_client, user):
    response = auth_client.get(reverse('change_password'))
    assert response.status_code == 200
    assert 'accounts/change_password.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form'], CustomPasswordChangeForm)

@pytest.mark.django_db
def test_change_password_view_post_valid(auth_client, user):
    response = auth_client.post(reverse('change_password'), {
        'old_password': 'testpass123',
        'new_password1': 'newpass123',
        'new_password2': 'newpass123'
    })
    assert response.status_code == 302
    assert response.url == reverse('login')
    user.refresh_from_db()
    assert user.check_password('newpass123')

@pytest.mark.django_db
def test_change_password_view_post_invalid(auth_client, user):
    response = auth_client.post(reverse('change_password'), {
        'old_password': 'wrongpass',
        'new_password1': 'newpass123',
        'new_password2': 'newpass123'
    })
    assert response.status_code == 200
    assert 'accounts/change_password.html' in [t.name for t in response.templates]
    assert 'form' in response.context
    assert not response.context['form'].is_valid()

@pytest.mark.django_db
def test_update_profile_view_get(auth_client, user):
    response = auth_client.get(reverse('profile'))
    assert response.status_code == 200
    assert 'accounts/profile.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form'], ProfileUpdateForm)

@pytest.mark.django_db
def test_update_profile_view_post_valid(auth_client, user):
    response = auth_client.post(reverse('profile'), {
        'username': 'updateduser',
        'email': 'updated@example.com',
        'phone_number': '1234567890',
        'birthday': '1990-01-01'
    })
    assert response.status_code == 302
    assert response.url == reverse('home')
    user.refresh_from_db()
    assert user.username == 'updateduser'
    assert user.email == 'updated@example.com'

@pytest.mark.django_db
def test_update_profile_view_post_invalid(auth_client, user):
    response = auth_client.post(reverse('profile'), {
        'username': 'updateduser',
        'email': 'invalid-email',
        'phone_number': '1234567890',
        'birthday': '1990-01-01'
    })
    assert response.status_code == 200
    assert 'accounts/profile.html' in [t.name for t in response.templates]
    assert 'form' in response.context
    assert not response.context['form'].is_valid()
