from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth import get_user_model
import json
import os
import tempfile
import logging

# Model imports
from .models import Document, DocumentInformation
from sharing.models import SharedDocument
from documents.models import ChatMessage

# Inference imports
from inference.inference import classify_document
from inference.inference_license_roboflow import extract_license_info
from inference.inference_check_roboflow import extract_check_info
from inference.inference_invoice_donut import run_information_extraction, run_docvqa
from inference.inference_passport_roboflow import extract_passport_info
from inference.inference_resume_roboflow import extract_resume_info

@login_required
def check_shared_status(request, doc_id):
    try:
        document = Document.objects.get(id=doc_id, uploaded_by=request.user)
        shared_docs = SharedDocument.objects.filter(document=document)
        if shared_docs.exists():
            User = get_user_model()
            username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'
            shared_with = shared_docs.values_list(f'shared_with__{username_field}', flat=True)
            shared_with_list = [username for username in shared_with if username is not None]
            return JsonResponse({
                'is_shared': True,
                'shared_with_count': len(shared_with_list),
                'shared_with_usernames': ', '.join(shared_with_list)
            })
        return JsonResponse({'is_shared': False})
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

logger = logging.getLogger(__name__)

# documents/views.py
@login_required(login_url='/login/')
def upload_document(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)

        # Create a temporary file with the proper extension
        file_extension = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        try:
            # Verify file exists before classification
            if not os.path.exists(temp_file_path):
                raise FileNotFoundError(f"Temporary file not created: {temp_file_path}")

            # Classify the document
            predicted_category = classify_document(temp_file_path)

            # Save document metadata to the database
            doc = Document(
                title=os.path.splitext(uploaded_file.name)[0],
                file=uploaded_file,
                file_type=file_extension,
                file_size=uploaded_file.size,
                category=predicted_category,
                uploaded_by=request.user
            )
            doc.save()

            # Handle extraction for each document category
            extracted_info = {}
            doc_info = None

            if predicted_category == "Check":
                try:
                    extracted_info = extract_check_info(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to extract check info: {str(e)}")
                    extracted_info = {"error": "Could not extract check information"}
                    doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                    doc_info.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Document classified as {predicted_category}, but information extraction failed.'
                    }, status=400)

            elif predicted_category == "License":
                try:
                    extracted_info = extract_license_info(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to extract license info: {str(e)}")
                    extracted_info = {"error": "Could not extract license information"}
                    doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                    doc_info.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Document classified as {predicted_category}, but information extraction failed.'
                    }, status=400)

            elif predicted_category == "Invoice":
                try:
                    extracted_info = run_information_extraction(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to extract invoice info: {str(e)}")
                    extracted_info = {"error": "Could not extract invoice information"}
                    doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                    doc_info.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Document classified as {predicted_category}, but information extraction failed.'
                    }, status=400)

            elif predicted_category == "Resume":
                try:
                    extracted_info = extract_resume_info(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to extract resume info: {str(e)}")
                    extracted_info = {"error": "Could not extract resume information"}
                    doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                    doc_info.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Document classified as {predicted_category}, but information extraction failed.'
                    }, status=400)

            elif predicted_category == "Passport":
                try:
                    extracted_info = extract_passport_info(temp_file_path)
                except Exception as e:
                    logger.error(f"Failed to extract passport info: {str(e)}")
                    extracted_info = {"error": "Could not extract passport information"}
                    doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                    doc_info.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Document classified as {predicted_category}, but information extraction failed.'
                    }, status=400)

            else:
                extracted_info = {"error": "Unsupported document category"}
                doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
                doc_info.save()
                return JsonResponse({
                    'status': 'error',
                    'message': 'Document classified as an unsupported category.'
                }, status=400)

            # If extraction succeeds, save the info and return success
            doc_info = DocumentInformation(document=doc, extracted_info=extracted_info)
            doc_info.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Document classified as {predicted_category} and information extracted successfully.',
                'document': {
                    'id': doc.id,
                    'title': doc.title,
                    'file_type': doc.file_type or 'Unknown',
                    'file_size': doc.file_size,
                    'category': doc.get_category_display(),  # Use display value for category
                    'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': doc.status if hasattr(doc, 'status') else 'Review'  # Include status
                }
            }, status=200)

        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            if 'doc' in locals():
                doc_info = DocumentInformation(
                    document=doc,
                    extracted_info={"error": "Could not process the uploaded file"}
                )
                doc_info.save()
            return JsonResponse({
                'status': 'error',
                'message': 'Could not process the uploaded file.'
            }, status=500)

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return render(request, 'accounts/home.html')

@login_required(login_url='/login/')
def document_list(request):
    documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    return render(request, 'documents/document_list.html', {'documents': documents})

# documents/views.py

@login_required(login_url='/login/')
def document_detail(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    
    has_access = document.uploaded_by == request.user
    has_edit_permission = False
    
    if not has_access:
        shared_doc = SharedDocument.objects.filter(
            document=document, 
            shared_with=request.user
        ).first()
        if shared_doc:
            has_access = True
            has_edit_permission = shared_doc.permission == 'edit'
        else:
            raise Http404("Document not found or access denied")
    else:
        has_edit_permission = True
    
    # Fetch extracted information
    doc_info = document.information.first()
    extracted_info = doc_info.extracted_info if doc_info else {}
    
    # Get chat history for invoices
    chat_history = ChatMessage.objects.filter(user=request.user, document=document) if document.category == 'Invoice' else []

    return render(request, 'documents/document_detail.html', {
        "document": document,
        "has_edit_permission": has_edit_permission,
        "extracted_info": extracted_info,
        "chat_history": chat_history
    })

def edit_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)
    if request.method == 'POST':
        if not SharedDocument.objects.filter(document=document).exists():
            title = request.POST.get('title', document.title)
            category = request.POST.get('category', document.category)
            document.title = title
            document.category = category
            document.save()
            messages.success(request, "Document updated successfully!")
        else:
            messages.error(request, "Cannot edit a shared document!")
        return redirect('home')
    # Change this path to where your template actually exists
    return render(request, 'documents/edit_document.html', {
        'document': document,
        'categories': Document.CATEGORY_CHOICES,
    })

@login_required(login_url='/login/')
def download_document(request, doc_id):
    
    # Get document or return 404
    document = get_object_or_404(Document, id=doc_id)
    
    # Check permissions
    has_access = request.user == document.uploaded_by or SharedDocument.objects.filter(
        document=document,
        shared_with=request.user
    ).exists()
    
    if not has_access:
        raise Http404("Document not found or access denied")
    
    # Check if the file exists
    if not document.file:
        return JsonResponse({'error': 'No file associated with this document'}, status=404)
    
    try:
        # Open the file in binary read mode
        file_handle = document.file.open('rb')
        # Ensure the file is closed after the response
        response = FileResponse(file_handle, as_attachment=True, filename=document.title)
        return response
    except FileNotFoundError:
        return JsonResponse({'error': 'File not found on server'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error downloading file: {str(e)}'}, status=500)

def fetch_document_data(request, doc_id):
    try:
        # Get document
        document = Document.objects.get(id=doc_id)
        
        # Check permissions
        if not (request.user == document.uploaded_by or
                SharedDocument.objects.filter(document=document, 
                                             shared_with=request.user).exists()):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Use select_related to optimize query
        doc_info = document.information.first()
        
        if not doc_info:
            return JsonResponse(
                {'error': 'Document exists but no extracted data found'},
                status=404
            )
            
        return JsonResponse(doc_info.extracted_info, safe=False)
        
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

@login_required
def update_document_data(request, doc_id):
    if request.method == 'POST':
        try:
            # Get the document
            document = Document.objects.get(id=doc_id)
            
            # Ensure the user has permission to edit this document
            has_edit_permission = document.uploaded_by == request.user or SharedDocument.objects.filter(
                document=document,
                shared_with=request.user,
                permission='edit'
            ).exists()
            
            if not has_edit_permission:
                return JsonResponse({'error': 'Not authorized'}, status=403)
            
            # Get the updated data from the request
            updated_data = json.loads(request.body)
            
            # Get the document information object
            doc_info = document.information.first()
            
            if not doc_info:
                # Create a new document information object if it doesn't exist
                doc_info = DocumentInformation(
                    document=document,
                    extracted_info=updated_data
                )
            else:
                # Update the existing document information
                doc_info.extracted_info = updated_data
            
            # Save the changes
            doc_info.save()
            
            return JsonResponse({'status': 'success'})
            
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

import logging
logger = logging.getLogger(__name__)

@login_required
def ask_document_question(request, doc_id):
    if request.method == "POST":
        document = get_object_or_404(Document, id=doc_id)
        if not (request.user == document.uploaded_by or
                SharedDocument.objects.filter(document=document, shared_with=request.user).exists()):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        try:
            data = json.loads(request.body)
            question = data.get("question", "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        if not question:
            return JsonResponse({"error": "No question provided"}, status=400)

        file_path = document.file.path
        answer = run_docvqa(file_path, question)

        # Save the chat message
        ChatMessage.objects.create(
            user=request.user,  # Works with CustomUser
            document=document,
            question=question,
            answer=answer
        )

        return JsonResponse({"answer": answer})
    return JsonResponse({"error": "Invalid request method"}, status=405)
