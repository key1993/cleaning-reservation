# One-liner PowerShell command to test notification
# Copy and paste this single line into PowerShell (modify values first):

Invoke-RestMethod -Uri "https://cleaning-reservation.onrender.com/api/send_notification_to_client" -Method Post -Body (@{user_email="client@example.com";user_id="507f1f77bcf86cd799439011";title="Test Notification";body="This is a test from PowerShell";data=@{type="admin_notification";source="admin_panel"}} | ConvertTo-Json) -ContentType "application/json"




