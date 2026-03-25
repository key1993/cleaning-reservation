#!/usr/bin/env python3
"""
Simple script to send FCM push notification to a client
Usage:
    python send_notification.py <fcm_token> <title> <body>
    
Example:
    python send_notification.py "cLwlLJzg6UHYgHGHy4-Xlu:APA91bE..." "Hello" "This is a test notification"
"""

import sys
import os
from firebase_service import send_fcm_notification, initialize_firebase

def send_notification(fcm_token, title, body, data=None):
    """
    Send a notification to a client
    
    Args:
        fcm_token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional dictionary of custom data
    """
    # Initialize Firebase if not already initialized
    initialize_firebase()
    
    # Send notification
    result = send_fcm_notification(
        fcm_token=fcm_token,
        title=title,
        body=body,
        data=data
    )
    
    if result.get("success"):
        print(f"✅ Notification sent successfully!")
        print(f"   Message ID: {result.get('message_id')}")
        return True
    else:
        print(f"❌ Failed to send notification: {result.get('error')}")
        return False

def main():
    """Main function to handle command line arguments"""
    
    # Check if running from command line with arguments
    if len(sys.argv) >= 4:
        fcm_token = sys.argv[1]
        title = sys.argv[2]
        body = sys.argv[3]
        
        # Optional data parameter (not implemented in CLI for simplicity)
        data = None
        
        send_notification(fcm_token, title, body, data)
    
    else:
        # Example usage - modify these values
        print("=" * 60)
        print("FCM Notification Sender")
        print("=" * 60)
        print()
        
        # ============================================
        # MODIFY THESE VALUES:
        # ============================================
        FCM_TOKEN = "YOUR_FCM_TOKEN_HERE"  # Replace with actual FCM token
        TITLE = "Test Notification"
        BODY = "This is a test notification from the backend"
        DATA = {
            "type": "test",
            "action": "open_app"
        }
        # ============================================
        
        if FCM_TOKEN == "YOUR_FCM_TOKEN_HERE":
            print("⚠️  Please set FCM_TOKEN in the script first!")
            print()
            print("Usage:")
            print("  python send_notification.py <fcm_token> <title> <body>")
            print()
            print("Or modify the FCM_TOKEN, TITLE, and BODY variables in the script.")
            sys.exit(1)
        
        print(f"Sending notification...")
        print(f"  Title: {TITLE}")
        print(f"  Body: {BODY}")
        print(f"  Token: {FCM_TOKEN[:20]}...")
        print()
        
        success = send_notification(FCM_TOKEN, TITLE, BODY, DATA)
        
        if success:
            print()
            print("✅ Done!")
        else:
            print()
            print("❌ Failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()





