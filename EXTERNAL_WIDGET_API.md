# External Widget API Integration Guide

## Overview
This document describes:
1. The API request format sent from the Admin Panel to your external widget when toggling the "Disable External Widget" feature
2. How your external widget can query its current enabled/disabled status from the server

## API Request Format

When an admin toggles the "Disable External Widget" checkbox for a client in the admin panel, the system will send a POST request to your external widget endpoint.

### Endpoint Configuration

The widget endpoint URL can be configured in two ways:

1. **Environment Variable** (Recommended):
   Set the `EXTERNAL_WIDGET_API_URL` environment variable to your widget's API endpoint:
   ```
   EXTERNAL_WIDGET_API_URL=https://your-widget-domain.com/api/widget/disable
   ```

2. **Automatic from HA URL**:
   If no environment variable is set, the system will automatically construct the URL from the client's Home Assistant URL:
   ```
   {ha_url}/api/widget/disable
   ```
   For example, if `ha_url` is `https://homeassistant.local:8123`, the endpoint will be:
   ```
   https://homeassistant.local:8123/api/widget/disable
   ```

### Request Details

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "client_id": "507f1f77bcf86cd799439011",
  "client_name": "John Doe",
  "disabled": true,
  "ha_token": "your-home-assistant-token",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### Field Descriptions

- **client_id** (string): The MongoDB ObjectId of the client record
- **client_name** (string): The full name of the client
- **disabled** (boolean): 
  - `true` = Widget should be disabled
  - `false` = Widget should be enabled
- **ha_token** (string): The Home Assistant access token for the client (for authentication)
- **timestamp** (string): ISO 8601 formatted UTC timestamp of when the request was made

### Example Request

**Disable Widget:**
```bash
curl -X POST https://your-widget-domain.com/api/widget/disable \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "507f1f77bcf86cd799439011",
    "client_name": "John Doe",
    "disabled": true,
    "ha_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "timestamp": "2024-01-15T10:30:00.123456"
  }'
```

**Enable Widget:**
```bash
curl -X POST https://your-widget-domain.com/api/widget/disable \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "507f1f77bcf86cd799439011",
    "client_name": "John Doe",
    "disabled": false,
    "ha_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "timestamp": "2024-01-15T10:35:00.123456"
  }'
```

### Expected Response

Your widget endpoint should return a JSON response:

**Success Response:**
```json
{
  "success": true,
  "message": "Widget disabled successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200 OK`: Request processed successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication failed (check ha_token)
- `404 Not Found`: Client/widget not found
- `500 Internal Server Error`: Server error

### Implementation Example (Python/Flask)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/widget/disable', methods=['POST'])
def handle_widget_disable():
    data = request.json
    
    client_id = data.get('client_id')
    client_name = data.get('client_name')
    is_disabled = data.get('disabled')
    ha_token = data.get('ha_token')
    
    # Verify authentication using ha_token
    if not verify_ha_token(ha_token):
        return jsonify({"success": False, "error": "Invalid token"}), 401
    
    # Update widget state
    if is_disabled:
        # Disable the widget
        disable_widget(client_id)
        return jsonify({"success": True, "message": "Widget disabled"}), 200
    else:
        # Enable the widget
        enable_widget(client_id)
        return jsonify({"success": True, "message": "Widget enabled"}), 200
```

### Implementation Example (JavaScript/Node.js)

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/widget/disable', (req, res) => {
  const { client_id, client_name, disabled, ha_token } = req.body;
  
  // Verify authentication
  if (!verifyHAToken(ha_token)) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  // Update widget state
  if (disabled) {
    disableWidget(client_id);
    res.json({ success: true, message: 'Widget disabled' });
  } else {
    enableWidget(client_id);
    res.json({ success: true, message: 'Widget enabled' });
  }
});
```

### Notes

1. **Timeout**: The admin panel will wait up to 10 seconds for a response from your widget endpoint.

2. **Error Handling**: If the widget endpoint is unreachable or returns an error, the admin panel will still update the database status. The error will be logged but won't prevent the operation.

3. **Security**: Make sure to verify the `ha_token` in your widget endpoint to ensure the request is legitimate.

4. **Idempotency**: Your endpoint should be idempotent - calling it multiple times with the same `disabled` value should have the same effect.

5. **Testing**: You can test your endpoint using the curl examples above or by toggling the checkbox in the admin panel.

---

## Querying Widget Status (For Your External Widget)

Your external widget can query its current enabled/disabled status from the server using a GET request.

### Endpoint

**URL:** `GET /api/widget/status`

**Base URL:** Your server's base URL (e.g., `https://your-server.com` or `https://your-server.com:5000`)

### Authentication

The widget must authenticate using the `ha_token` (Home Assistant token) associated with the client. You can provide it in two ways:

**Option 1: Query Parameter (Recommended)**
```
GET /api/widget/status?ha_token=YOUR_HA_TOKEN
```

**Option 2: Authorization Header**
```
GET /api/widget/status
Authorization: Bearer YOUR_HA_TOKEN
```

### Full API Request Examples

**Using Query Parameter:**
```bash
curl -X GET "https://your-server.com/api/widget/status?ha_token=eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json"
```

**Using Authorization Header:**
```bash
curl -X GET "https://your-server.com/api/widget/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**JavaScript/Fetch Example:**
```javascript
const haToken = 'your-home-assistant-token';
const serverUrl = 'https://your-server.com';

// Using query parameter
fetch(`${serverUrl}/api/widget/status?ha_token=${haToken}`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      if (data.disabled) {
        console.log('Widget is DISABLED');
        // Hide or disable your widget UI
      } else {
        console.log('Widget is ENABLED');
        // Show or enable your widget UI
      }
    } else {
      console.error('Error:', data.error);
    }
  })
  .catch(error => console.error('Request failed:', error));

// Using Authorization header
fetch(`${serverUrl}/api/widget/status`, {
  headers: {
    'Authorization': `Bearer ${haToken}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => {
    // Handle response
  });
```

**Python Example:**
```python
import requests

ha_token = "your-home-assistant-token"
server_url = "https://your-server.com"

# Using query parameter
response = requests.get(
    f"{server_url}/api/widget/status",
    params={"ha_token": ha_token}
)

# Using Authorization header
response = requests.get(
    f"{server_url}/api/widget/status",
    headers={"Authorization": f"Bearer {ha_token}"}
)

data = response.json()

if data.get("success"):
    if data.get("disabled"):
        print("Widget is DISABLED")
        # Disable your widget
    else:
        print("Widget is ENABLED")
        # Enable your widget
else:
    print(f"Error: {data.get('error')}")
```

### Response Format

**Success Response (200 OK):**
```json
{
  "success": true,
  "client_id": "507f1f77bcf86cd799439011",
  "client_name": "John Doe",
  "disabled": false,
  "enabled": true,
  "status": "enabled",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "ha_token is required. Provide it as query parameter 'ha_token' or in Authorization header as 'Bearer <token>'"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Client not found with the provided ha_token"
}
```

### Response Field Descriptions

- **success** (boolean): Whether the request was successful
- **client_id** (string): The MongoDB ObjectId of the client record
- **client_name** (string): The full name of the client
- **disabled** (boolean): `true` if widget is disabled, `false` if enabled
- **enabled** (boolean): `true` if widget is enabled, `false` if disabled (opposite of `disabled`)
- **status** (string): Either `"enabled"` or `"disabled"` (human-readable status)
- **timestamp** (string): ISO 8601 formatted UTC timestamp of when the status was queried

### Recommended Usage Pattern

Your widget should periodically check its status (e.g., every 30-60 seconds) to ensure it stays in sync with the admin panel:

```javascript
// Check widget status every 30 seconds
setInterval(async () => {
  try {
    const response = await fetch(`${serverUrl}/api/widget/status?ha_token=${haToken}`);
    const data = await response.json();
    
    if (data.success) {
      updateWidgetVisibility(data.disabled);
    }
  } catch (error) {
    console.error('Failed to check widget status:', error);
  }
}, 30000); // Check every 30 seconds

function updateWidgetVisibility(isDisabled) {
  const widgetElement = document.getElementById('your-widget');
  if (isDisabled) {
    widgetElement.style.display = 'none';
    // Or disable widget functionality
  } else {
    widgetElement.style.display = 'block';
    // Or enable widget functionality
  }
}
```

### HTTP Status Codes

- `200 OK`: Request successful, status returned
- `400 Bad Request`: Missing or invalid `ha_token` parameter
- `404 Not Found`: No client found with the provided `ha_token`
- `500 Internal Server Error`: Server error

---

## Admin Panel Usage

1. Navigate to the Admin Panel
2. Click on the "Clients" tab
3. Find the client you want to manage
4. In the "Disable External Widget" column, check/uncheck the checkbox
5. Confirm the action in the popup dialog
6. The system will send the API request to your widget endpoint

## Troubleshooting

- **Widget not receiving requests**: Check that `EXTERNAL_WIDGET_API_URL` is set correctly or that the HA URL is valid
- **Authentication errors**: Verify that the `ha_token` is correct and your endpoint validates it properly
- **Timeout errors**: Ensure your widget endpoint responds within 10 seconds
- **Check server logs**: The admin panel logs all widget API requests and responses

