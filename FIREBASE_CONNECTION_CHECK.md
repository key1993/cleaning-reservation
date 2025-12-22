# Firebase Connection Verification Guide

## Quick Checklist

Use this guide to verify that Firebase is correctly connected to your admin panel.

## 1. Check Firebase Initialization on Server Start

When your server starts, you should see one of these messages in the logs:

**✅ Success:**
```
✅ Firebase Admin SDK initialized successfully
```

**❌ Failure:**
```
⚠️ Firebase initialization failed: [error message]
Payment reminder system will work, but account disabling will be unavailable
```

**Action:** Check your server logs (Render logs) when the app starts to see which message appears.

## 2. Test Firebase Connection Endpoint

After logging into the admin panel, visit:
```
https://cleaning-reservation.onrender.com/admin/test_firebase_connection
```

**Expected Success Response:**
```json
{
  "success": true,
  "message": "Firebase connection successful",
  "users_found": 5,
  "users": [
    {
      "uid": "abc123...",
      "email": "user@example.com",
      "disabled": false,
      "email_verified": true
    },
    ...
  ]
}
```

**Expected Failure Response:**
```json
{
  "success": false,
  "error": "Firebase is not initialized",
  "details": "Check FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON environment variable"
}
```

## 3. Verify Environment Variables

Check that Firebase credentials are configured in your Render dashboard:

### Option A: Using File Path
- **Variable Name:** `FIREBASE_CREDENTIALS_PATH`
- **Value:** Path to your Firebase service account JSON file
- Example: `/opt/render/project/src/firebase-credentials.json`

### Option B: Using JSON String (Recommended for Render)
- **Variable Name:** `FIREBASE_CREDENTIALS_JSON`
- **Value:** The entire contents of your Firebase service account JSON file as a string

**How to get Firebase credentials:**
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Download the JSON file
4. Copy the entire JSON content and paste it as the value for `FIREBASE_CREDENTIALS_JSON`

## 4. Test Firebase Functions in Admin Panel

Try these actions in the admin panel to verify Firebase connectivity:

### Test 1: Link Firebase Account by Email
1. Go to Admin Panel → Clients tab
2. Find a client without Firebase UID
3. Click "Link by Email"
4. Enter an email that exists in Firebase
5. **Expected:** Should find and link the Firebase account

### Test 2: Enable/Disable Account
1. Find a client with Firebase UID
2. Click "Firebase Actions" dropdown
3. Click "Enable Account" or "Disable Account"
4. **Expected:** Should successfully enable/disable the Firebase account

### Test 3: Reset Password
1. Find a client with Firebase UID
2. Click "Firebase Actions" → "Reset Password"
3. **Expected:** Should generate a temporary password

### Test 4: Delete Account
1. Find a client with Firebase UID
2. Click "Firebase Actions" → "Delete Account"
3. **Expected:** Should delete the Firebase account

## 5. Check Server Logs for Errors

When performing Firebase actions, check your server logs for:

**✅ Success Messages:**
```
✅ Firebase user [uid] enabled successfully
✅ Firebase user [uid] disabled successfully
✅ Password reset for Firebase user [uid]
✅ Firebase user [uid] deleted successfully
```

**❌ Error Messages:**
```
⚠️ Firebase user [uid] not found
❌ Error [action] Firebase user [uid]: [error details]
❌ Firebase not initialized. Cannot [action] user.
```

## 6. Verify Firebase Service Account Permissions

Ensure your Firebase service account has these permissions:
- **Firebase Authentication Admin** role
- Ability to read/write user accounts
- Ability to manage user authentication

## 7. Common Issues and Solutions

### Issue: "Firebase is not initialized"
**Solution:**
- Check that `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_PATH` is set in Render
- Verify the JSON content is valid
- Restart your Render service after setting environment variables

### Issue: "User not found"
**Solution:**
- Verify the email exists in Firebase Console → Authentication → Users
- Check for typos in the email
- Ensure the email is exactly as shown in Firebase Console

### Issue: "Permission denied" or "Unauthorized"
**Solution:**
- Verify Firebase service account has correct permissions
- Regenerate the service account key
- Ensure you're using the correct Firebase project

### Issue: Functions work but email search doesn't
**Solution:**
- Check server logs for detailed error messages
- Verify email format (no extra spaces, correct case)
- Try using the Firebase UID directly instead of email

## 8. Manual Verification Steps

1. **Check Render Environment Variables:**
   - Go to Render Dashboard → Your Service → Environment
   - Verify `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_PATH` exists

2. **Check Firebase Console:**
   - Go to Firebase Console → Authentication → Users
   - Verify users exist and can be managed

3. **Test with cURL:**
   ```bash
   curl https://cleaning-reservation.onrender.com/admin/test_firebase_connection
   ```
   (Requires admin login session)

## 9. Quick Test Script

You can test Firebase connection using PowerShell:

```powershell
# Test Firebase connection (requires admin login)
$response = Invoke-RestMethod -Uri "https://cleaning-reservation.onrender.com/admin/test_firebase_connection" -Method Get
$response | ConvertTo-Json
```

## Summary

✅ **Firebase is correctly connected if:**
- Server logs show "✅ Firebase Admin SDK initialized successfully"
- `/admin/test_firebase_connection` returns user list
- Firebase actions (enable/disable/reset/delete) work in admin panel
- No error messages in server logs

❌ **Firebase is NOT connected if:**
- Server logs show initialization failed
- Test endpoint returns "Firebase is not initialized"
- Firebase actions fail with initialization errors
- Environment variables are missing

