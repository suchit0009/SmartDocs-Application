from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.contrib.auth import logout
from .forms import CustomUserCreationForm, ProfileUpdateForm, CustomPasswordChangeForm
from .utils import handle_login_errors
from documents.models import Document
from sharing.models import SharedDocument

# Landing Page view
def landing(request):
    return render(request, 'accounts/landing.html')

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if handle_login_errors(request, form, username, password):
                user = authenticate(request, username=username, password=password)
                login(request, user)
                messages.success(request, "Successfully logged in!")
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


# Register View
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new custom user
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')  # Redirect to login after registration
        else:
            # Handle specific errors
            messages.error(request, "Registration failed. Please check the errors below.")
            print(form.errors)  # Print errors to the console for debugging
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

# Home Page view
@login_required
def home(request):
    search_query = request.GET.get('search', '').strip()
    
    all_documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')

    # Print all document
    print(f"All documents for user {request.user.username}: {all_documents.count()} documents found.")  # Debug

    license_docs = Document.objects.filter(uploaded_by=request.user, category='License').order_by('-uploaded_at')
    passport_docs = Document.objects.filter(uploaded_by=request.user, category='Passport').order_by('-uploaded_at')
    invoice_docs = Document.objects.filter(uploaded_by=request.user, category='Invoice').order_by('-uploaded_at')
    check_docs = Document.objects.filter(uploaded_by=request.user, category='Check').order_by('-uploaded_at')
    resume_docs = Document.objects.filter(uploaded_by=request.user, category='Resume').order_by('-uploaded_at')

    if search_query:
        all_documents = all_documents.filter(title__icontains=search_query)

    latest_documents = all_documents[:4]
    latest_passport_docs = passport_docs[:4]
    latest_invoice_docs = invoice_docs[:4]
    latest_check_docs = check_docs[:4]
    latest_resume_docs = resume_docs[:4]
    latest_license_docs = license_docs[:4]

    sort = request.GET.get('sort', 'uploaded_at')
    order = request.GET.get('order', 'desc')

    if sort == 'file_size':
        all_documents = all_documents.annotate(
            file_size_non_null=Coalesce('file_size', Value(0))
        )
        order_prefix = '' if order == 'asc' else '-'
        all_documents = all_documents.order_by(f'{order_prefix}file_size_non_null')
    elif sort == 'uploaded_at':
        order_prefix = '' if order == 'asc' else '-'
        all_documents = all_documents.order_by(f'{order_prefix}{sort}')

    paginator = Paginator(all_documents, 5)
    page_number = request.GET.get('page')
    all_documents_page = paginator.get_page(page_number)

    shared_docs = SharedDocument.objects.filter(shared_with=request.user).order_by('-shared_at')
    latest_shared_docs = shared_docs[:4]

    

    if search_query:
        license_docs = license_docs.filter(title__icontains=search_query)
        passport_docs = passport_docs.filter(title__icontains=search_query)
        invoice_docs = invoice_docs.filter(title__icontains=search_query)
        check_docs = check_docs.filter(title__icontains=search_query)
        resume_docs = resume_docs.filter(title__icontains=search_query)

    total_documents = all_documents.count()
    license_count = license_docs.count()
    passport_count = passport_docs.count()
    invoice_count = invoice_docs.count()
    check_count = check_docs.count()
    resume_count = resume_docs.count()
    shared_count = shared_docs.count()

    if request.method == 'POST' and 'delete_document' in request.POST:
        doc_id = request.POST.get('doc_id')
        try:
            document = Document.objects.get(id=doc_id, uploaded_by=request.user)
            doc_title = document.title  # Store the title before deletion

            # Check if the document is shared
            shared_docs = SharedDocument.objects.filter(document=document)
            print(f"SharedDocument records for document {doc_id}: {shared_docs.count()}")  # Debug

            if not shared_docs.exists():
                document.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Document deleted successfully',
                    'document_title': doc_title
                })
            else:
                # Determine the username field dynamically
                User = get_user_model()
                username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'
                print(f"Username field: {username_field}")  # Debug

                # Get the list of usernames of users the document is shared with
                shared_with_query = shared_docs.values_list(f'shared_with__{username_field}', flat=True)
                shared_with_list = list(shared_with_query)
                shared_count = len(shared_with_list)

                # Debug: Log the shared users
                print(f"Shared with users: {shared_with_list}, Count: {shared_count}")

                document.delete()  # This will also delete related SharedDocument records due to CASCADE

                # Construct the message based on whether there are shared users
                if shared_count > 0:
                    message = f'Document deleted, affecting {shared_count} shared user(s): {", ".join(shared_with_list)}'
                else:
                    message = 'Document deleted successfully (shared with 0 users).'

                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'document_title': doc_title
                })
        except Document.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Document not found'}, status=404)

    context = {
        'latest_documents': latest_documents,
        'latest_license_docs': latest_license_docs,
        'latest_passport_docs': latest_passport_docs,
        'latest_invoice_docs': latest_invoice_docs,
        'latest_check_docs': latest_check_docs,
        'latest_resume_docs': latest_resume_docs,
        'all_documents_page': all_documents_page,
        'shared_docs': shared_docs,
        'latest_shared_docs': latest_shared_docs,
        'sort': sort,
        'order': order,
        'total_documents': total_documents,
        'license_docs': license_docs,
        'passport_docs': passport_docs,
        'invoice_docs': invoice_docs,
        'check_docs': check_docs,
        'resume_docs': resume_docs,
        'license_count': license_count,
        'passport_count': passport_count,
        'invoice_count': invoice_count,
        'check_count': check_count,
        'resume_count': resume_count,
        'shared_count': shared_count,
        'search_query': search_query,
    }
    return render(request, 'accounts/home.html', context)




# API to get a list of users
def user_list_api(request):
    User = get_user_model()
    users = User.objects.all()
    data = []
    for user in users:
        data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
        })
    return JsonResponse(data, safe=False)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user out after password change
            logout(request)
            messages.success(request, 'Your password was successfully updated! Please log in with your new password.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
        
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


