# accounts/utils.py
from django.contrib import messages
from django.contrib.auth import authenticate

def handle_login_errors(request, form, username, password):
    """Handle common login errors and set appropriate messages"""
    if not username and not password:
        messages.error(request, "Please enter both username and password")
        return False
    
    if not username:
        messages.error(request, "Username is required")
        return False
    
    if not password:
        messages.error(request, "Password is required")
        return False
    
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, "Invalid username or password")
        return False
        
    if not user.is_active:
        messages.error(request, "This account is inactive")
        return False
        
    return True

