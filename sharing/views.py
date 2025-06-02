from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from documents.models import Document
from .models import SharedDocument
import json
import logging


logger = logging.getLogger(__name__)
User = get_user_model()

@login_required
def share_document(request, document_id):
    """Share a document with selected users"""
    logger.debug(f"Attempting to share document with ID: {document_id}")
    
    document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
    
    try:
        # Parse JSON safely
        data = json.loads(request.body)
        user_ids = data.get('users')
        permission = data.get('permission')
        
        logger.debug(f"Received data: user_ids={user_ids}, permission={permission}")
        
        if not user_ids:
            return JsonResponse({'error': 'User list cannot be empty'}, status=400)
        if permission not in ['view', 'edit']:
            return JsonResponse({'error': 'Invalid permission. Allowed values are "view" and "edit".'}, status=400)
        
        # Fetch all users in one query
        users = User.objects.filter(id__in=user_ids)
        logger.debug(f"Found {users.count()} users: {[user.username for user in users]}")
        
        users_dict = {user.id: user for user in users}  # Create a lookup dictionary
        
        results = []
        for user_id in user_ids:
            user_id = int(user_id)  # Convert to integer if it's a string
            user = users_dict.get(user_id)
            if not user:
                results.append({'user_id': user_id, 'status': 'error', 'message': 'User not found'})
                continue  # Skip this user
            
            # Debug the model field names to ensure they match
            logger.debug(f"Creating SharedDocument with document={document}, shared_with={user}, shared_by={request.user}, permission={permission}")
            
            # Create or update sharing permissions
            try:
                shared_doc, created = SharedDocument.objects.update_or_create(
                    document=document,
                    shared_with=user,
                    defaults={'shared_by': request.user, 'permission': permission}
                )
                logger.debug(f"SharedDocument {'created' if created else 'updated'}: {shared_doc.id}")
            except Exception as e:
                logger.error(f"Error creating/updating SharedDocument: {str(e)}")
                results.append({'user_id': user_id, 'status': 'error', 'message': str(e)})
                continue
            
            results.append({
                'user_id': user_id,
                'status': 'created' if created else 'updated',
                'permission': permission
            })
        
        logger.debug(f"Document {document.title} sharing results: {results}")
        
        return JsonResponse({'success': True, 'results': results, 'message': f'Document shared with {len(results)} users'})
    
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Error sharing document: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def shared_documents(request):
    """Get documents shared with the current user"""
    shared_docs = SharedDocument.objects.filter(shared_with=request.user).select_related('document', 'shared_by')

    documents = [
        {
            'id': shared.document.id,
            'title': shared.document.title,
            'category': shared.document.category,
            'shared_by': shared.shared_by.username,
            'permission': shared.permission,
            'shared_at': shared.shared_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for shared in shared_docs
    ]

    return JsonResponse({'success': True, 'documents': documents})