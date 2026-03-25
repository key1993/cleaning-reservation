#!/usr/bin/env python3
"""
Direct Firebase FCM notification sender
Sends notification directly to Firebase, bypassing the backend API
"""

import os
import firebase_admin
from firebase_admin import credentials, messaging

# ============================================
# CONFIGURATION - MODIFY THESE VALUES:
# ============================================
FCM_TOKEN = "YOUR_FCM_TOKEN_HERE"  # Replace with actual FCM token
TITLE = "Direct FCM Test"
BODY = "This notification is sent directly to Firebase"
# ============================================

# Initialize Firebase Admin SDK
def initialize_firebase_direct():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        if firebase_admin._apps:
            return firebase_admin.get_app()
        
        # Get Firebase credentials from environment variable or file
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        
        if cred_path and os.path.exists(cred_path):
            # Use service account JSON file
            cred = credentials.Certificate(cred_path)
            # Extract project_id from credentials if not explicitly set
            if not project_id:
                import json
                with open(cred_path, 'r') as f:
                    cred_data = json.load(f)
                    project_id = cred_data.get('project_id')
            
            if project_id:
                app = firebase_admin.initialize_app(cred, {'projectId': project_id})
            else:
                app = firebase_admin.initialize_app(cred)
        elif cred_json:
            # Use JSON string from environment variable
            import json
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            # Extract project_id from credentials if not explicitly set
            if not project_id:
                project_id = cred_dict.get('project_id')
            
            if project_id:
                app = firebase_admin.initialize_app(cred, {'projectId': project_id})
            else:
                app = firebase_admin.initialize_app(cred)
        else:
            # Try default credentials
            project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if project_id:
                app = firebase_admin.initialize_app(options={'projectId': project_id})
            else:
                print("❌ No Firebase credentials found. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON")
                return None
        
        print("✅ Firebase Admin SDK initialized")
        if project_id:
            print(f"   Project ID: {project_id}")
        return app
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# Send FCM notification directly
def send_fcm_direct(fcm_token, title, body, data=None):
    """
    Send FCM notification directly to Firebase
    
    Args:
        fcm_token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional custom data dictionary
    """
    try:
        # Initialize Firebase
        app = initialize_firebase_direct()
        if not app:
            print("❌ Cannot send: Firebase not initialized")
            return False
        
        if not fcm_token or fcm_token == "YOUR_FCM_TOKEN_HERE":
            print("❌ Please set FCM_TOKEN")
            return False
        
        # Prepare data (FCM requires all values to be strings)
        fcm_data = {}
        if data:
            for key, value in data.items():
                fcm_data[str(key)] = str(value) if value is not None else ""
        
        # Build the FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=fcm_data,
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high'
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            )
        )
        
        print(f"📤 Sending FCM notification directly to Firebase...")
        print(f"   Token: {fcm_token[:20]}...")
        print(f"   Title: {title}")
        print(f"   Body: {body}")
        
        # Send directly to Firebase
        response = messaging.send(message)
        
        print(f"✅ FCM notification sent successfully!")
        print(f"   Message ID: {response}")
        return True
        
    except ValueError as e:
        if "Unregistered" in str(e) or "unregistered" in str(e).lower():
            print(f"⚠️ FCM token is unregistered (device may have uninstalled app)")
        else:
            print(f"❌ Invalid argument: {e}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "Unregistered" in error_msg or "unregistered" in error_msg.lower():
            print(f"⚠️ FCM token is unregistered (device may have uninstalled app)")
        elif "Invalid" in error_msg or "invalid" in error_msg.lower():
            print(f"❌ Invalid FCM token or argument: {e}")
        else:
            print(f"❌ Error sending FCM notification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Direct Firebase FCM Notification Sender")
    print("=" * 60)
    print()
    
    # Optional custom data
    custom_data = {
        "type": "direct_test",
        "source": "python_script"
    }
    
    # Send notification
    success = send_fcm_direct(
        fcm_token=FCM_TOKEN,
        title=TITLE,
        body=BODY,
        data=custom_data
    )
    
    if success:
        print()
        print("✅ Done!")
    else:
        print()
        print("❌ Failed!")
        exit(1)

