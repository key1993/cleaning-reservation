# How to Link Your Firebase Account - Step by Step Guide

This guide will walk you through linking your Firebase account to the website so you can manage user accounts.

## Step 1: Access Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Sign in with your Google account
3. Select your Firebase project (or create a new one if needed)

## Step 2: Enable Authentication (if not already enabled)

1. In Firebase Console, click on **"Authentication"** in the left sidebar
2. If Authentication is not enabled, click **"Get Started"**
3. Click on the **"Sign-in method"** tab
4. Enable the authentication methods you need (Email/Password, etc.)

## Step 3: Create Service Account for Admin SDK

1. In Firebase Console, click the **gear icon** (⚙️) next to "Project Overview"
2. Click on **"Project settings"**
3. Go to the **"Service accounts"** tab
4. Click **"Generate new private key"**
5. A confirmation dialog will appear - click **"Generate key"**
6. A JSON file will be downloaded to your computer (e.g., `your-project-firebase-adminsdk-xxxxx.json`)

⚠️ **IMPORTANT**: Keep this file secure! It gives full admin access to your Firebase project.

## Step 4: Save the Credentials File

### Option A: Local Development (Windows)

1. Create a folder for your credentials (e.g., `C:\firebase-credentials\`)
2. Move the downloaded JSON file to this folder
3. Rename it to something simple like `firebase-credentials.json`

### Option B: Cloud/Production Deployment

For production (Render, Heroku, etc.), you'll need to use environment variables instead of a file.

## Step 5: Set Environment Variable

### For Windows (PowerShell):

```powershell
# Replace the path with your actual file path
$env:FIREBASE_CREDENTIALS_PATH="C:\firebase-credentials\firebase-credentials.json"
```

### For Windows (Command Prompt):

```cmd
set FIREBASE_CREDENTIALS_PATH=C:\firebase-credentials\firebase-credentials.json
```

### To Make it Permanent (Windows):

1. Open **System Properties** → **Environment Variables**
2. Click **"New"** under User variables
3. Variable name: `FIREBASE_CREDENTIALS_PATH`
4. Variable value: `C:\firebase-credentials\firebase-credentials.json`
5. Click **OK** to save

### For Linux/Mac:

```bash
export FIREBASE_CREDENTIALS_PATH="/path/to/firebase-credentials.json"
```

### For Production (Cloud Platforms):

Use your hosting platform's environment variable settings:

**Render:**
1. Go to your service settings
2. Environment → Add Environment Variable
3. Key: `FIREBASE_CREDENTIALS_JSON`
4. Value: Paste the entire JSON file content (as a single line)

**Heroku:**
```bash
heroku config:set FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

## Step 6: Install Firebase Admin SDK

Make sure you have the Firebase Admin SDK installed:

```bash
pip install firebase-admin
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 7: Verify the Connection

1. Start your Flask application:
   ```bash
   python app.py
   ```

2. Check the console output. You should see:
   ```
   ✅ Firebase Admin SDK initialized successfully
   ```

3. If you see an error, check:
   - File path is correct
   - File has proper read permissions
   - JSON file is valid

## Step 8: Link Client Accounts to Firebase

### Method 1: Using "Link by Email" Button

1. Go to your Admin Panel
2. Find a client without a Firebase UID
3. Click **"Link by Email"** button
4. Enter the email address the user used to register in Firebase
5. The system will find and link the account automatically

### Method 2: Using API Endpoint

You can also link accounts programmatically:

```bash
POST /search_firebase_user
Body: {
  "email": "user@example.com",
  "client_id": "mongodb_client_id"
}
```

### Method 3: Manual UID Entry

If you know the Firebase UID:

```bash
POST /update_client_firebase_uid/<client_id>
Body: {
  "firebase_uid": "firebase-user-uid-here"
}
```

## Troubleshooting

### ❌ Error: "Firebase not initialized"

**Solution:**
- Check that `FIREBASE_CREDENTIALS_PATH` environment variable is set
- Verify the file path is correct
- Make sure the file exists and is readable

### ❌ Error: "Invalid credentials"

**Solution:**
- Ensure the JSON file is valid (not corrupted)
- Verify you downloaded the correct service account key
- Check that the file hasn't been modified

### ❌ Error: "Permission denied"

**Solution:**
- Make sure the service account has proper permissions
- In Firebase Console → IAM & Admin → check service account permissions
- Service account should have "Firebase Admin" role

### ❌ Can't find user by email

**Solution:**
- Verify the user exists in Firebase Authentication
- Check the email spelling exactly matches
- Make sure Authentication is enabled in Firebase Console

## Security Best Practices

1. **Never commit credentials to Git**
   - Add to `.gitignore`: `firebase-credentials.json`
   - Use environment variables in production

2. **Restrict file permissions**
   - Only your application should read the credentials file

3. **Rotate keys regularly**
   - Generate new keys periodically for security

4. **Use separate projects**
   - Use one Firebase project for development
   - Use another for production

## Testing Your Setup

1. Link a test client to Firebase
2. Try disabling their account
3. Verify in Firebase Console → Authentication that the account is disabled
4. Re-enable the account and verify it works

## Next Steps

Once linked, the system will:
- ✅ Automatically disable accounts when payments are overdue
- ✅ Automatically enable accounts when payment is confirmed
- ✅ Allow you to manually manage accounts from the admin panel

## Need Help?

Check the server logs for detailed error messages. The system will log:
- Firebase initialization status
- Account disable/enable operations
- Any errors encountered

