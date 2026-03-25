# Flask Backend Updates for Mobile App

To make your Flask backend work with the Flutter iOS app, you need to add CORS support.

## Step 1: Install flask-cors

```bash
pip install flask-cors
```

## Step 2: Update app.py

Add CORS to your Flask app. Update your `app.py` file:

```python
from flask import Flask
from flask_cors import CORS  # Add this import

# ... your other imports ...

app = Flask(__name__)

# Add CORS support - place this right after creating the Flask app
CORS(app, supports_credentials=True, origins=["*"])

# For production, you may want to restrict origins:
# CORS(app, supports_credentials=True, origins=[
#     "http://localhost:5000",
#     "https://your-production-domain.com"
# ])

# ... rest of your code ...
```

## Step 3: Update Session Configuration (Optional)

If you're having issues with sessions, you may want to configure Flask sessions for cross-origin requests:

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
```

## Step 4: Test the Backend

1. Start your Flask backend:
   ```bash
   python app.py
   ```

2. Test with curl or Postman:
   ```bash
   curl -X POST http://localhost:5000/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"test"}' \
     -v
   ```

   Check that the response includes CORS headers:
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Credentials`

## Notes

- The mobile app uses the same API endpoints as your web app
- Sessions are handled via cookies
- Make sure your Flask backend is accessible from your iOS device/emulator
- For physical devices, use your computer's IP address instead of `localhost`

## Production Considerations

1. **HTTPS**: Use HTTPS in production
2. **CORS Origins**: Restrict CORS origins to your app's domain
3. **Session Security**: Enable secure cookies in production:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   ```

That's it! Your Flask backend should now work with the Flutter iOS app.






