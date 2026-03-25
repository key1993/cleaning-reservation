#!/usr/bin/env python3
"""
Super simple script to send FCM notification
Just modify the values below and run: python send_notification_simple.py
"""

from firebase_service import send_fcm_notification, initialize_firebase

# ============================================
# MODIFY THESE VALUES:
# ============================================
FCM_TOKEN = "YOUR_FCM_TOKEN_HERE"  # Replace with actual FCM token
TITLE = "Hello! 👋"
BODY = "This is a test notification"
# ============================================

# Initialize Firebase
initialize_firebase()

# Send notification
result = send_fcm_notification(
    fcm_token=FCM_TOKEN,
    title=TITLE,
    body=BODY,
    data={"type": "test"}  # Optional custom data
)

# Check result
if result.get("success"):
    print(f"✅ Notification sent successfully!")
    print(f"   Message ID: {result.get('message_id')}")
else:
    print(f"❌ Failed: {result.get('error')}")





