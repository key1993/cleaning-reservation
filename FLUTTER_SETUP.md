# Flutter iOS App Setup Guide

## Quick Start

Your Flask web application has been successfully converted to a Flutter iOS app! Here's how to get it running:

## Step 1: Install Flutter

1. Download Flutter from: https://flutter.dev/docs/get-started/install
2. Follow the installation guide for macOS
3. Verify installation: `flutter doctor`

## Step 2: Configure Flask Backend for Mobile

Your Flask backend needs CORS enabled to accept requests from the mobile app. Add this to your `app.py`:

```python
from flask_cors import CORS

# Add this after creating your Flask app
CORS(app, supports_credentials=True, origins=["*"])  # In production, specify your app's origin
```

Also install flask-cors:
```bash
pip install flask-cors
```

## Step 3: Set Up Flutter App

1. **Navigate to Flutter app:**
   ```bash
   cd flutter_app
   ```

2. **Install dependencies:**
   ```bash
   flutter pub get
   ```

3. **Configure API URL:**
   - Open `lib/services/api_service.dart`
   - Find line with `static const String baseUrl`
   - Update it:
     - For iOS Simulator: `'http://localhost:5000'`
     - For physical device: `'http://YOUR_COMPUTER_IP:5000'` (e.g., `'http://192.168.1.100:5000'`)
     - For production: `'https://your-backend-url.com'`

4. **iOS Setup:**
   ```bash
   cd ios
   pod install
   cd ..
   ```

## Step 4: Configure Location Permissions

1. Open `ios/Runner/Info.plist`
2. Add these keys (if not present):
   ```xml
   <key>NSLocationWhenInUseUsageDescription</key>
   <string>We need your location to create reservations</string>
   <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
   <string>We need your location to create reservations</string>
   ```

## Step 5: Run the App

1. **Start your Flask backend:**
   ```bash
   python app.py
   ```

2. **Run Flutter app:**
   ```bash
   flutter run
   ```

   Or specify iOS:
   ```bash
   flutter run -d ios
   ```

## Features Included

✅ **User Features:**
- Login/Register
- Create reservations with GPS location
- View reservation history
- Profile management

✅ **Admin Features:**
- Admin login
- View all reservations
- Approve/Deny reservations
- Client management
- Payment tracking
- Payment confirmation

## Design

The app matches your web design:
- Same purple gradient (`#667eea` to `#764ba2`)
- Same admin pink/red gradient (`#f093fb` to `#f5576c`)
- Modern, clean UI

## Building for Production

1. **Build iOS app:**
   ```bash
   flutter build ios --release
   ```

2. **Open in Xcode:**
   ```bash
   open ios/Runner.xcworkspace
   ```

3. **In Xcode:**
   - Select your Apple Developer account
   - Configure signing & capabilities
   - Archive → Distribute App → App Store Connect

## Troubleshooting

### "Connection refused" Error
- Make sure Flask backend is running
- Check `baseUrl` in `api_service.dart`
- For physical device, use your computer's IP address, not `localhost`
- Ensure firewall allows connections

### Location Not Working
- Check Info.plist has location permissions
- Enable location services on device
- Check app permissions in iOS Settings

### Session/Cookie Issues
- Flask sessions use cookies - ensure CORS is configured correctly
- You may need to adjust cookie handling in `api_service.dart` based on your Flask session configuration

## Next Steps

1. Add your logo to `assets/images/logo.png`
2. Test all features thoroughly
3. Customize UI as needed
4. Add push notifications (optional)
5. Submit to App Store

## File Structure

```
flutter_app/
├── lib/
│   ├── main.dart              # Entry point
│   ├── models/               # Data models
│   ├── services/             # API services
│   ├── providers/            # State management
│   └── screens/              # UI screens
├── pubspec.yaml              # Dependencies
└── README.md                 # Detailed docs
```

## Need Help?

- Flutter docs: https://flutter.dev/docs
- Check Flask backend logs for API errors
- Check Xcode console for iOS errors






