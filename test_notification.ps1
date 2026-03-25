# PowerShell script to test sending FCM notification
# Copy and paste this entire script into PowerShell

$url = "https://cleaning-reservation.onrender.com/api/send_notification_to_client"

# ============================================
# MODIFY THESE VALUES:
# ============================================
$userEmail = "client@example.com"  # Replace with actual client email
$userId = "507f1f77bcf86cd799439011"  # Replace with actual client ID (optional)
$title = "Test Notification"
$body = "This is a test notification from PowerShell"
# ============================================

# Create the request body
$bodyJson = @{
    user_email = $userEmail
    user_id = $userId
    title = $title
    body = $body
    data = @{
        type = "admin_notification"
        source = "admin_panel"
    }
} | ConvertTo-Json

# Set headers
$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "Sending notification..." -ForegroundColor Yellow
Write-Host "URL: $url" -ForegroundColor Cyan
Write-Host "Email: $userEmail" -ForegroundColor Cyan
Write-Host "Title: $title" -ForegroundColor Cyan
Write-Host "Body: $body" -ForegroundColor Cyan
Write-Host ""

try {
    # Send the request
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $bodyJson -Headers $headers -ContentType "application/json"
    
    # Display result
    if ($response.success) {
        Write-Host "✅ Notification sent successfully!" -ForegroundColor Green
        Write-Host "   Message ID: $($response.message_id)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Full response:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 10
    } else {
        Write-Host "❌ Failed to send notification" -ForegroundColor Red
        Write-Host "   Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}




