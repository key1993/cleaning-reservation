# Firebase Integration Setup Guide

This guide will help you set up Firebase Admin SDK to enable automatic account disabling for overdue payments.

## Prerequisites

1. A Firebase project (create one at https://console.firebase.google.com/)
2. Firebase Admin SDK service account credentials

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select an existing project
3. Follow the setup wizard

## Step 2: Generate Service Account Key

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Click on the **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the JSON file securely (e.g., `firebase-credentials.json`)

## Step 3: Configure Environment Variables

You have two options to provide Firebase credentials:

### Option A: Using a File Path (Recommended for Local Development)

Set the environment variable:
```bash
export FIREBASE_CREDENTIALS_PATH="/path/to/firebase-credentials.json"
```

Or in Windows PowerShell:
```powershell
$env:FIREBASE_CREDENTIALS_PATH="C:\path\to\firebase-credentials.json"
```

### Option B: Using JSON String (Recommended for Production/Cloud)

Set the environment variable with the JSON content:
```bash
export FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'
```

**Important:** Never commit the credentials file to Git! Add it to `.gitignore`:
```
firebase-credentials.json
*.json
```

## Step 4: Link Firebase UID to Clients

For each client in your system, you need to link their Firebase UID. You can do this:

1. **Manually via Admin Panel**: Use the API endpoint `/update_client_firebase_uid/<client_id>` with POST request containing `firebase_uid`
2. **During Client Registration**: Update the `register_client` route to accept and store `firebase_uid`

## Step 5: Install Dependencies

```bash
pip install firebase-admin
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## How It Works

### Automatic Account Disabling

- The payment reminder system runs daily at 9:00 AM
- When a payment is overdue (past the `next_payment_date`), the system will:
  1. Send a WhatsApp reminder
  2. Automatically disable the Firebase account (if Firebase UID is linked)
  3. Mark the account as disabled in MongoDB

### Automatic Account Re-enabling

- When payment is confirmed via the admin panel:
  1. The system automatically re-enables the Firebase account
  2. Updates the payment date
  3. Sends a confirmation message

### Manual Account Management

- In the admin panel, you can manually:
  - **Disable Account**: Click "Disable Account" button for any client
  - **Enable Account**: Click "Enable Account" button for disabled clients
  - **View Status**: See account status (Active/Disabled) in the clients table

## API Endpoints

### Disable Client Account
```
POST /disable_client_account/<client_id>
```

### Enable Client Account
```
POST /enable_client_account/<client_id>
```

### Update Firebase UID
```
POST /update_client_firebase_uid/<client_id>
Body: {"firebase_uid": "firebase-user-uid"}
```

## Troubleshooting

### Firebase Not Initialized
- Check that `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_CREDENTIALS_JSON` is set
- Verify the credentials file path is correct
- Ensure the JSON file is valid

### Account Not Disabling
- Verify the client has a `firebase_uid` field in MongoDB
- Check that the Firebase UID is valid
- Review server logs for error messages

### Permission Errors
- Ensure the service account has "Firebase Admin" permissions
- Check that the service account key is not expired

## Security Notes

1. **Never commit credentials to Git**
2. **Use environment variables in production**
3. **Restrict access to service account keys**
4. **Regularly rotate service account keys**
5. **Monitor Firebase Admin API usage**

## Testing

To test the integration:

1. Create a test client with a Firebase UID
2. Set their `next_payment_date` to a past date
3. Manually trigger payment reminders: `GET /check_payment_reminders`
4. Verify the Firebase account is disabled
5. Confirm payment and verify the account is re-enabled

