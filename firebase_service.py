"""
Firebase Admin SDK service for managing user accounts
"""
import os
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK
firebase_app = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    global firebase_app
    
    if firebase_app is not None:
        return firebase_app
    
    # Get Firebase credentials from environment variable or file
    cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    
    if cred_path and os.path.exists(cred_path):
        # Use service account JSON file
        cred = credentials.Certificate(cred_path)
        firebase_app = firebase_admin.initialize_app(cred)
    elif os.environ.get("FIREBASE_CREDENTIALS_JSON"):
        # Use JSON string from environment variable
        import json
        cred_dict = json.loads(os.environ.get("FIREBASE_CREDENTIALS_JSON"))
        cred = credentials.Certificate(cred_dict)
        firebase_app = firebase_admin.initialize_app(cred)
    else:
        # Try default credentials (for Google Cloud environments)
        try:
            firebase_app = firebase_admin.initialize_app()
        except Exception as e:
            print(f"Warning: Firebase not initialized. Error: {e}")
            print("Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON environment variable")
            return None
    
    return firebase_app

def disable_firebase_user(firebase_uid):
    """
    Disable a Firebase user account by UID
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            print("Firebase not initialized. Cannot disable user.")
            return False
        
        # Disable the user account
        auth.update_user(
            firebase_uid,
            disabled=True
        )
        print(f"✅ Firebase user {firebase_uid} disabled successfully")
        return True
        
    except auth.UserNotFoundError:
        print(f"⚠️ Firebase user {firebase_uid} not found")
        return False
    except Exception as e:
        print(f"❌ Error disabling Firebase user {firebase_uid}: {e}")
        return False

def enable_firebase_user(firebase_uid):
    """
    Enable a Firebase user account by UID
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            print("Firebase not initialized. Cannot enable user.")
            return False
        
        # Enable the user account
        auth.update_user(
            firebase_uid,
            disabled=False
        )
        print(f"✅ Firebase user {firebase_uid} enabled successfully")
        return True
        
    except auth.UserNotFoundError:
        print(f"⚠️ Firebase user {firebase_uid} not found")
        return False
    except Exception as e:
        print(f"❌ Error enabling Firebase user {firebase_uid}: {e}")
        return False

def get_firebase_user(firebase_uid):
    """
    Get Firebase user information by UID
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        UserRecord or None
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            return None
        
        return auth.get_user(firebase_uid)
        
    except Exception as e:
        print(f"❌ Error getting Firebase user {firebase_uid}: {e}")
        return None

def delete_firebase_user(firebase_uid):
    """
    Delete a Firebase user account by UID
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            print("Firebase not initialized. Cannot delete user.")
            return False
        
        # Delete the user account
        auth.delete_user(firebase_uid)
        print(f"✅ Firebase user {firebase_uid} deleted successfully")
        return True
        
    except auth.UserNotFoundError:
        print(f"⚠️ Firebase user {firebase_uid} not found")
        return False
    except Exception as e:
        print(f"❌ Error deleting Firebase user {firebase_uid}: {e}")
        return False

def get_firebase_user_by_email(email):
    """
    Get Firebase user by email address
    
    Args:
        email: User email address
        
    Returns:
        UserRecord or None
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            return None
        
        user = auth.get_user_by_email(email)
        return user
        
    except auth.UserNotFoundError:
        print(f"⚠️ Firebase user with email {email} not found")
        return None
    except Exception as e:
        print(f"❌ Error getting Firebase user by email {email}: {e}")
        return None

def create_firebase_user(email, password, display_name=None, phone_number=None):
    """
    Create a new Firebase user account
    
    Args:
        email: User email
        password: User password
        display_name: Optional display name
        phone_number: Optional phone number
        
    Returns:
        UserRecord or None
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            return None
        
        user_data = {
            'email': email,
            'password': password,
            'email_verified': False,
            'disabled': False
        }
        
        if display_name:
            user_data['display_name'] = display_name
        if phone_number:
            user_data['phone_number'] = phone_number
        
        user = auth.create_user(**user_data)
        print(f"✅ Firebase user created: {user.uid}")
        return user
        
    except Exception as e:
        print(f"❌ Error creating Firebase user: {e}")
        return None

