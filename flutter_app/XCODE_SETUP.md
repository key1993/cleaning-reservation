# Xcode Setup Guide

## ⚠️ Important: The iOS platform files need to be generated first!

Your Flutter app code is ready, but you need to generate the iOS platform files before opening in Xcode.

## Step-by-Step Setup

### Step 1: Generate iOS Platform Files

Run this command in the `flutter_app` directory:

```bash
cd flutter_app
flutter create --platforms=ios .
```

This will generate all the necessary iOS files (Xcode project, Podfile, Info.plist, etc.) while keeping your existing Dart code.

### Step 2: Install Dependencies

```bash
flutter pub get
cd ios
pod install
cd ..
```

### Step 3: Configure Location Permissions

After generating the iOS files, you need to add location permissions:

1. Open `ios/Runner/Info.plist`
2. Add these keys inside the `<dict>` tag:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>We need your location to create reservations</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>We need your location to create reservations</string>
```

### Step 4: Configure API URL

1. Open `lib/services/api_service.dart`
2. Update the `baseUrl`:
   - For iOS Simulator: `'http://localhost:5000'`
   - For physical device: `'http://YOUR_COMPUTER_IP:5000'`

### Step 5: Open in Xcode

```bash
open ios/Runner.xcworkspace
```

**Important:** Always open `.xcworkspace`, NOT `.xcodeproj`

### Step 6: Configure Signing in Xcode

1. In Xcode, select the **Runner** project in the left sidebar
2. Select the **Runner** target
3. Go to **Signing & Capabilities** tab
4. Check **"Automatically manage signing"**
5. Select your **Team** (Apple Developer account)
6. Xcode will automatically configure signing

### Step 7: Run the App

- Press **⌘ + R** (or click the Play button) to run
- Or select a simulator/device from the device dropdown

## Quick Setup Script

You can run these commands all at once:

```bash
cd flutter_app
flutter create --platforms=ios .
flutter pub get
cd ios && pod install && cd ..
```

Then configure Info.plist and api_service.dart as described above.

## Troubleshooting

### "No iOS platform found"
- Run `flutter create --platforms=ios .` in the flutter_app directory

### "Pod install failed"
- Make sure CocoaPods is installed: `sudo gem install cocoapods`
- Try: `cd ios && pod deintegrate && pod install`

### "Signing error"
- Make sure you have an Apple Developer account
- Check "Automatically manage signing" in Xcode
- Select your team

### "Build failed"
- Clean build: `flutter clean && flutter pub get`
- In Xcode: Product → Clean Build Folder (⇧⌘K)

## After Setup

Once everything is set up, you can:
- ✅ Open in Xcode: `open ios/Runner.xcworkspace`
- ✅ Build and run from Xcode
- ✅ Archive for App Store distribution
- ✅ Test on simulator or physical device

Your Dart code is already complete and ready - you just need the iOS platform files!






