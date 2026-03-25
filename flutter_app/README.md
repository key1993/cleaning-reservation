# EBSHER - Cleaning Reservation iOS App

A Flutter iOS application for managing cleaning reservations, built to work with your existing Flask backend.

## Features

- ✅ User Authentication (Login/Register)
- ✅ Create and manage reservations
- ✅ Location-based reservations using GPS
- ✅ View reservation history
- ✅ Admin dashboard
- ✅ Client management
- ✅ Payment tracking
- ✅ Beautiful, modern UI matching your web design

## Setup Instructions

### Prerequisites

1. **Flutter SDK**: Install Flutter from [flutter.dev](https://flutter.dev/docs/get-started/install)
2. **Xcode**: Required for iOS development (Mac only)
3. **CocoaPods**: Usually installed automatically with Xcode

### Installation

1. **Navigate to the Flutter app directory:**
   ```bash
   cd flutter_app
   ```

2. **Install dependencies:**
   ```bash
   flutter pub get
   ```

3. **Configure API endpoint:**
   - Open `lib/services/api_service.dart`
   - Update the `baseUrl` constant with your Flask backend URL:
     ```dart
     static const String baseUrl = 'http://your-backend-url.com';
     ```
   - For local development: `'http://localhost:5000'`
   - For production: `'https://your-production-url.com'`

4. **iOS Setup:**
   ```bash
   cd ios
   pod install
   cd ..
   ```

5. **Configure Location Permissions:**
   - Open `ios/Runner/Info.plist`
   - Add location permissions (if not already present):
     ```xml
     <key>NSLocationWhenInUseUsageDescription</key>
     <string>We need your location to create reservations</string>
     <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
     <string>We need your location to create reservations</string>
     ```

### Running the App

1. **Connect your iOS device** or start the iOS Simulator

2. **Run the app:**
   ```bash
   flutter run
   ```

   Or specify iOS:
   ```bash
   flutter run -d ios
   ```

### Building for Production

1. **Build iOS app:**
   ```bash
   flutter build ios
   ```

2. **Open in Xcode:**
   ```bash
   open ios/Runner.xcworkspace
   ```

3. **In Xcode:**
   - Select your development team
   - Configure signing & capabilities
   - Archive and distribute through App Store Connect

## Project Structure

```
flutter_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── models/                   # Data models
│   │   ├── user.dart
│   │   ├── reservation.dart
│   │   └── client.dart
│   ├── services/                 # API and services
│   │   ├── api_service.dart     # Flask backend API client
│   │   └── auth_service.dart    # Authentication service
│   ├── providers/                # State management
│   │   ├── auth_provider.dart
│   │   ├── reservation_provider.dart
│   │   └── admin_provider.dart
│   └── screens/                  # UI screens
│       ├── splash_screen.dart
│       ├── auth/
│       │   ├── login_screen.dart
│       │   └── register_screen.dart
│       ├── user/
│       │   ├── dashboard_screen.dart
│       │   └── create_reservation_screen.dart
│       └── admin/
│           ├── admin_login_screen.dart
│           └── admin_dashboard_screen.dart
├── pubspec.yaml                  # Dependencies
└── README.md
```

## API Configuration

The app connects to your Flask backend. Make sure:

1. **CORS is enabled** on your Flask backend for mobile requests
2. **Session management** works correctly (the app uses cookies for sessions)
3. **Base URL** is correctly set in `api_service.dart`

### Flask Backend CORS Setup

Add this to your Flask `app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
```

## Features Overview

### User Features
- **Login/Register**: Secure authentication
- **Create Reservations**: Select date, time, and get GPS location
- **View Reservations**: See all your reservations with status
- **Profile Management**: View and update profile

### Admin Features
- **Admin Login**: Separate admin authentication
- **Reservation Management**: View, approve, deny reservations
- **Client Management**: View clients, track payments
- **Payment Confirmation**: Mark payments as received
- **Bulk Operations**: Delete multiple reservations/clients

## Troubleshooting

### Common Issues

1. **"Connection refused" error:**
   - Check that your Flask backend is running
   - Verify the `baseUrl` in `api_service.dart`
   - For iOS Simulator, use `http://localhost:5000`
   - For physical device, use your computer's IP: `http://192.168.x.x:5000`

2. **Location not working:**
   - Check Info.plist has location permissions
   - Ensure location services are enabled on device
   - Check app permissions in iOS Settings

3. **Build errors:**
   - Run `flutter clean`
   - Run `flutter pub get`
   - In iOS folder: `pod deintegrate && pod install`

## Design

The app uses the same color scheme as your web app:
- Primary: `#667eea` (Purple gradient)
- Secondary: `#764ba2`
- Admin: `#f5576c` (Pink/Red gradient)

## Next Steps

1. Add your logo asset to `assets/images/`
2. Configure push notifications (optional)
3. Add more features as needed
4. Test thoroughly on physical devices
5. Submit to App Store

## Support

For issues or questions, check:
- Flutter documentation: https://flutter.dev/docs
- Your Flask backend logs
- iOS console logs in Xcode






