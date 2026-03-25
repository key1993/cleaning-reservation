@echo off
REM Flutter iOS Setup Script for Windows
REM Note: iOS development requires macOS. This script is for reference.

echo Flutter iOS Setup Script
echo.
echo WARNING: iOS development requires macOS and Xcode.
echo This script should be run on a Mac.
echo.
echo If you're on Windows, you'll need to:
echo 1. Transfer the flutter_app folder to a Mac
echo 2. Run the setup commands there
echo.
echo Setup commands to run on Mac:
echo   cd flutter_app
echo   flutter create --platforms=ios .
echo   flutter pub get
echo   cd ios
echo   pod install
echo   cd ..
echo.
echo Then:
echo   1. Open ios/Runner/Info.plist and add location permissions
echo   2. Update lib/services/api_service.dart with your backend URL
echo   3. Open in Xcode: open ios/Runner.xcworkspace
echo.
pause






