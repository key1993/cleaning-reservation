# External Widget API Integration Guide

## Overview
This document describes the API request format that is sent from the Admin Panel to your external widget when toggling the "Disable External Widget" feature.

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

