"""
Utility functions for authentication.
"""

import re
from user_agents import parse


def get_client_ip(request):
    """
    Extract client IP address from request.
    Handles proxy forwarded IPs.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_device_info(request):
    """
    Extract device information from user agent.
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        user_agent = parse(user_agent_string)
        
        device = user_agent.device.family
        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
        os = f"{user_agent.os.family} {user_agent.os.version_string}"
        
        return f"{device} - {browser} on {os}"
    except:
        return "Unknown Device"


def is_strong_password(password):
    """
    Check if password meets strength requirements.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True


def generate_username_from_email(email):
    """
    Generate a unique username from email.
    """
    username = email.split('@')[0]
    username = re.sub(r'[^a-zA-Z0-9_]', '', username)
    return username[:30]  # Max 30 characters
