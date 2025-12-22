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
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    project_id = os.environ.get("FIREBASE_PROJECT_ID")  # Optional explicit project ID
    
    try:
        if cred_path and os.path.exists(cred_path):
            # Use service account JSON file
            cred = credentials.Certificate(cred_path)
            # Extract project_id from credentials if not explicitly set
            if not project_id:
                import json
                with open(cred_path, 'r') as f:
                    cred_data = json.load(f)
                    project_id = cred_data.get('project_id')
            
            # Initialize with explicit project_id
            if project_id:
                firebase_app = firebase_admin.initialize_app(cred, {
                    'projectId': project_id
                })
            else:
                firebase_app = firebase_admin.initialize_app(cred)
                
        elif cred_json:
            # Use JSON string from environment variable
            import json
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            
            # Extract project_id from credentials if not explicitly set
            if not project_id:
                project_id = cred_dict.get('project_id')
            
            # Initialize with explicit project_id
            if project_id:
                firebase_app = firebase_admin.initialize_app(cred, {
                    'projectId': project_id
                })
            else:
                firebase_app = firebase_admin.initialize_app(cred)
                
        else:
            # Try default credentials (for Google Cloud environments)
            project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if project_id:
                firebase_app = firebase_admin.initialize_app(options={
                    'projectId': project_id
                })
            else:
                firebase_app = firebase_admin.initialize_app()
        
        print(f"✅ Firebase Admin SDK initialized successfully")
        if project_id:
            print(f"   Project ID: {project_id}")
        return firebase_app
        
    except Exception as e:
        print(f"⚠️ Firebase initialization failed: {e}")
        print("Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON environment variable")
        print("Or set FIREBASE_PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable")
        return None

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
            print("❌ Firebase not initialized. Cannot search for user.")
            return None
        
        # Normalize email: trim whitespace and convert to lowercase
        # Firebase email lookups are case-insensitive, but we normalize for consistency
        normalized_email = email.strip().lower()
        
        print(f"🔍 Searching for Firebase user with email: {normalized_email}")
        
        # Try exact match first
        try:
            user = auth.get_user_by_email(normalized_email)
            print(f"✅ Found Firebase user: {user.uid} ({user.email})")
            return user
        except auth.UserNotFoundError:
            # Try with original case (in case Firebase stores it differently)
            try:
                user = auth.get_user_by_email(email.strip())
                print(f"✅ Found Firebase user with original case: {user.uid} ({user.email})")
                return user
            except auth.UserNotFoundError:
                print(f"⚠️ Firebase user with email '{email}' not found")
                print(f"   Tried normalized: '{normalized_email}'")
                print(f"   Tried original: '{email.strip()}'")
                return None
        
    except Exception as e:
        print(f"❌ Error getting Firebase user by email '{email}': {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
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

def reset_firebase_user_password(firebase_uid):
    """
    Generate a password reset link for a Firebase user
    
    Args:
        firebase_uid: Firebase user UID
        
    Returns:
        str: Password reset link or None if failed
    """
    try:
        if firebase_app is None:
            initialize_firebase()
        
        if firebase_app is None:
            print("Firebase not initialized. Cannot reset password.")
            return None
        
        # Get user to verify they exist
        user = auth.get_user(firebase_uid)
        
        # Generate password reset link
        # Note: This requires Firebase Admin SDK with proper configuration
        # For email-based reset, you would typically use Firebase Auth REST API
        # or send a password reset email through Firebase Console
        
        # Alternative: Generate a temporary password and update user
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Update user with temporary password
        auth.update_user(firebase_uid, password=temp_password)
        
        print(f"✅ Password reset for Firebase user {firebase_uid}")
        return temp_password
        
    except auth.UserNotFoundError:
        print(f"⚠️ Firebase user {firebase_uid} not found")
        return None
    except Exception as e:
        print(f"❌ Error resetting password for Firebase user {firebase_uid}: {e}")
        return None

