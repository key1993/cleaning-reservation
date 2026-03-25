# Quick Start - Get Running in Xcode

## ⚡ Fast Setup (5 minutes)

### 1. Generate iOS Files
```bash
cd flutter_app
flutter create --platforms=ios .
```

### 2. Install Dependencies
```bash
flutter pub get
cd ios && pod install && cd ..
```

### 3. Add Location Permissions

Edit `ios/Runner/Info.plist` - add inside `<dict>`:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>We need your location to create reservations</string>
```

### 4. Configure API URL

Edit `lib/services/api_service.dart` - line 11:

```dart
static const String baseUrl = 'http://localhost:5000';  // Change this!
```

### 5. Open in Xcode
```bash
open ios/Runner.xcworkspace
```

### 6. In Xcode:
- Select **Runner** project → **Runner** target
- **Signing & Capabilities** tab
- Check **"Automatically manage signing"**
- Select your **Team**
- Press **⌘ + R** to run!

## ✅ Done!

Your app should now run in Xcode. See `XCODE_SETUP.md` for detailed troubleshooting.






