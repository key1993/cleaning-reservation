#!/bin/bash

# Flutter iOS Setup Script
# This script generates iOS platform files and sets up the project for Xcode

echo "🚀 Setting up Flutter iOS app for Xcode..."

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed. Please install Flutter first:"
    echo "   https://flutter.dev/docs/get-started/install"
    exit 1
fi

echo "✅ Flutter found"

# Check if we're in the right directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Error: pubspec.yaml not found. Please run this script from the flutter_app directory."
    exit 1
fi

echo "📦 Generating iOS platform files..."
flutter create --platforms=ios .

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate iOS platform files"
    exit 1
fi

echo "✅ iOS platform files generated"

echo "📥 Installing Flutter dependencies..."
flutter pub get

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Flutter dependencies"
    exit 1
fi

echo "✅ Flutter dependencies installed"

echo "📦 Installing CocoaPods dependencies..."
cd ios
pod install

if [ $? -ne 0 ]; then
    echo "⚠️  CocoaPods installation had issues. You may need to run 'pod install' manually."
    echo "   Make sure CocoaPods is installed: sudo gem install cocoapods"
fi

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Open ios/Runner/Info.plist and add location permissions"
echo "   2. Update lib/services/api_service.dart with your backend URL"
echo "   3. Open in Xcode: open ios/Runner.xcworkspace"
echo "   4. Configure signing in Xcode (Signing & Capabilities tab)"
echo ""
echo "📖 See XCODE_SETUP.md for detailed instructions"






