# PowerShell script to send FCM notification directly via Firebase REST API
# This calls Firebase's REST API directly (not your backend)

# ============================================
# CONFIGURATION - MODIFY THESE VALUES:
# ============================================
$FCM_TOKEN = "YOUR_FCM_TOKEN_HERE"  # Replace with actual FCM token
$FIREBASE_SERVER_KEY = "YOUR_FIREBASE_SERVER_KEY"  # Get from Firebase Console > Project Settings > Cloud Messaging
$PROJECT_ID = "YOUR_PROJECT_ID"  # Your Firebase project ID

$TITLE = "Direct FCM Test"
$BODY = "This notification is sent directly to Firebase REST API"
# ============================================

# Firebase FCM REST API endpoint
$url = "https://fcm.googleapis.com/v1/projects/$PROJECT_ID/messages:send"

# Build the FCM message payload
$messagePayload = @{
    message = @{
        token = $FCM_TOKEN
        notification = @{
            title = $TITLE
            body = $BODY
        }
        data = @{
            type = "direct_test"
            source = "powershell"
        }
        android = @{
            priority = "high"
        }
        apns = @{
            payload = @{
                aps = @{
                    sound = "default"
                    badge = 1
                }
            }
        }
    }
} | ConvertTo-Json -Depth 10

# For REST API, you need OAuth2 token (complex)
# OR use Legacy HTTP API (simpler but deprecated):
$legacyUrl = "https://fcm.googleapis.com/fcm/send"

$legacyPayload = @{
    to = $FCM_TOKEN
    notification = @{
        title = $TITLE
        body = $BODY
    }
    data = @{
        type = "direct_test"
        source = "powershell"
    }
    priority = "high"
} | ConvertTo-Json -Depth 10

$headers = @{
    "Authorization" = "key=$FIREBASE_SERVER_KEY"
    "Content-Type" = "application/json"
}

Write-Host "Sending FCM notification directly to Firebase..." -ForegroundColor Yellow
Write-Host "Token: $($FCM_TOKEN.Substring(0, [Math]::Min(20, $FCM_TOKEN.Length)))..." -ForegroundColor Cyan
Write-Host ""

try {
    # Use Legacy HTTP API (simpler, but requires Server Key)
    $response = Invoke-RestMethod -Uri $legacyUrl -Method Post -Body $legacyPayload -Headers $headers
    
    if ($response.success) {
        Write-Host "✅ FCM notification sent successfully!" -ForegroundColor Green
        Write-Host "   Message ID: $($response.message_id)" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to send notification" -ForegroundColor Red
    }
    
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}



