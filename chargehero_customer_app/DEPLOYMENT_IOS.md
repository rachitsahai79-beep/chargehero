# ChargeHero Customer App - iOS Deployment to App Store

## Prerequisites

- macOS with Xcode 14+
- Flutter SDK 3.16.0+
- Apple Developer account ($99/year)
- App Store Connect access
- Apple Developer certificate and provisioning profile
- iPad or iPhone for testing

## App Store Connect Setup

### 1. Create App in App Store Connect

1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Click "Apps" in sidebar
3. Click "+" button to create new app
4. Select "New App":
   - Platform: iOS
   - Name: "ChargeHero"
   - Primary Language: English
   - Bundle ID: `com.chargehero.customer`
   - SKU: `chargehero-customer`
5. Click "Create"

### 2. App Information

Fill in required information:

**Pricing and Availability**
- Price Tier: Free
- Availability: Select India and other target markets
- Release date: Automatic (will release when approved)

**App Category**
- Category: Business
- Subcategory: Utilities

**Ratings**
- Alcohol/Tobacco: None
- Gambling: None
- Medical/Health: None
- Physical Threats: None
- Profanity: None
- Sexual Content: None
- Violence: None
- Other: None

## Code Signing & Certificates

### 1. Generate Signing Request

In Xcode:
1. Xcode > Preferences > Accounts
2. Select Apple ID
3. Click "Manage Certificates"
4. Click "+" to create new certificate
5. Select "Apple Distribution"
6. Download certificate
7. Double-click to install in Keychain

### 2. Create Provisioning Profile

1. Go to Apple Developer > Certificates, Identifiers & Profiles
2. Click "Profiles" in sidebar
3. Click "+" to create new profile
4. Select "App Store Connect"
5. Select Bundle ID: `com.chargehero.customer`
6. Select certificate (from step 1)
7. Download profile
8. Double-click to install in Xcode

### 3. Configure Signing in Xcode

```bash
cd chargehero_customer_app/ios

# Open in Xcode
open Runner.xcworkspace

# In Xcode:
# 1. Select Runner project
# 2. Select Runner target
# 3. Go to Signing & Capabilities
# 4. Verify team is selected
# 5. Verify provisioning profile is selected
# 6. Ensure "Automatically manage signing" is checked (for development)
```

## App Configuration

### Update Version Number

Edit `ios/Runner/Info.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- ... other config -->
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <!-- ... other config -->
</dict>
</plist>
```

Also update `pubspec.yaml`:

```yaml
version: 1.0.0+1  # iOS version+build
```

### Configure Build Settings

Edit `ios/Podfile`:

```ruby
# Deployment target must match or exceed iOS 12
post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '12.0'
    end
  end
end
```

## Build for App Store

### 1. Build Archive

```bash
cd chargehero_customer_app

# Clean build
flutter clean

# Get dependencies
flutter pub get

# Build iOS
flutter build ios --release

# Build archive in Xcode
cd ios
xcodebuild -workspace Runner.xcworkspace \
  -scheme Runner \
  -configuration Release \
  -derivedDataPath build \
  -archivePath build/Runner.xcarchive \
  archive

cd ..
```

### 2. Export IPA

```bash
cd ios

# Create export options plist
cat > ExportOptions.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>destination</key>
    <string>export</string>
    <key>method</key>
    <string>app-store</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
</dict>
</plist>
EOF

# Export IPA
xcodebuild -exportArchive \
  -archivePath build/Runner.xcarchive \
  -exportPath build/Runner.ipa \
  -exportOptionsPlist ExportOptions.plist

cd ..
```

### 3. Validate and Upload

Using Transporter:

```bash
# Download and install Transporter
# https://apps.apple.com/us/app/transporter/id1450874784

# Or use xcrun:
xcrun altool --upload-app \
  -f "ios/build/Runner.ipa" \
  -t ios \
  -u "your-apple-id@example.com" \
  -p "your-app-specific-password"
```

## App Store Submission

### 1. Fill App Information

In App Store Connect:

1. **App Information**
   - Localization (English)
   - Subtitle: "EV Charger Support"
   - Promotional text: "Get instant support for your EV charger"

2. **Screenshot & Preview**
   - Upload 2-5 screenshots (1170x2532px for iPhone)
   - Add descriptive text for each
   - App Preview video (optional, 30 seconds)

3. **Description**
   ```
   ChargeHero provides 24/7 support for EV charging issues.
   
   Get instant assistance with:
   - Real-time engineer dispatch
   - Live tracking
   - Troubleshooting help
   - Service reports
   
   Available in India.
   ```

4. **Keywords**
   - EV charging
   - Charger support
   - Electric vehicle
   - 24/7 support
   - Indian chargers

5. **Support URL**
   - https://chargehero.com/support

6. **Privacy Policy**
   - https://chargehero.com/privacy

7. **Licensing Agreement**
   - Accept standard terms

### 2. Build Information

- Select build from TestFlight
- Confirm build number matches

### 3. General App Information

- App Icon: 1024x1024px
- Copyright Notice: "© 2026 ChargeHero Inc."
- Contact Information: support@chargehero.com

### 4. Submit for Review

Click "Submit for Review" and select:
- Content rights: Confirm you own content
- Advertising ID: Check if using IDFA
- Export compliance: No cryptography

## TestFlight Beta Testing

### 1. Add Build to TestFlight

1. Upload IPA to App Store Connect
2. Wait for processing (5-10 minutes)
3. Build appears in TestFlight section

### 2. Create Beta Testing Groups

1. Internal Testing:
   - Add up to 25 team members
   - No review required
   - Immediate access

2. External Testing:
   - Add up to 10,000 beta testers
   - 1-24 hours review
   - Share public link

### 3. Manage Beta Testers

```bash
# Add testers via email
# In App Store Connect > TestFlight > Builds

# Send invitations
# Testers download TestFlight app
# Install app from TestFlight for testing
```

## Monitoring & Updates

### App Analytics

Track in App Store Connect:

- Impressions (views in App Store)
- Page Views
- Conversions (downloads)
- Installs
- Active Devices
- Retention
- Crashes

### Updates

For each new version:

1. Increment version: `1.0.0` → `1.1.0`
2. Build and archive
3. Submit for review
4. Review takes 12-48 hours
5. Once approved, automatic or manual release

## Troubleshooting

### Build Fails

```
Error: "Signing is required for product type 'Application'"

Solution:
1. Check Xcode signing settings
2. Verify certificate in Keychain
3. Verify provisioning profile
4. Check team ID matches
```

### Upload Fails

```
Error: "Invalid IPA: No code signature with supported algorithm found"

Solution:
1. Verify code signing in Xcode
2. Verify all frameworks are signed
3. Check deployment target matches
4. Use latest Xcode version
```

### App Rejected

Common rejections and solutions:

| Issue | Solution |
|-------|----------|
| Privacy policy missing | Add privacy policy URL |
| Crashes on startup | Test thoroughly, fix bugs |
| Inappropriate content | Review content rating |
| Misleading description | Update description accurately |
| Performance issues | Optimize app, reduce size |

## Release Process

### Phased Release (Optional)

Apple allows 7-day phased release:

1. Week 1: 5% of users
2. Week 2: 25% if stable
3. Week 3: 50% if stable
4. After 1 week: 100% if stable

Monitor crash rates during phased rollout.

### Manual Release

1. Submit version with "Manual Release"
2. After approval, click "Release This Version"
3. App becomes available immediately

## Security Best Practices

### App Transport Security

Update `ios/Runner/Info.plist`:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoadsInMedia</key>
    <false/>
    <key>NSAllowsArbitraryLoadsInWebContent</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>api.chargehero.com</key>
        <dict>
            <key>NSIncludesSubdomains</key>
            <true/>
            <key>NSTemporaryExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSTemporaryExceptionMinimumTLSVersion</key>
            <string>TLSv1.2</string>
        </dict>
    </dict>
</dict>
```

### Certificate Pinning

Implement certificate pinning in your HTTP client to prevent MITM attacks (see Android deployment guide for implementation details).

## Version Management

### Increment Versions

1. Update `pubspec.yaml`:
   ```yaml
   version: 1.1.0+2  # major.minor.patch+build
   ```

2. Update `ios/Runner/Info.plist`:
   ```xml
   <key>CFBundleShortVersionString</key>
   <string>1.1.0</string>
   <key>CFBundleVersion</key>
   <string>2</string>
   ```

3. Commit changes:
   ```bash
   git tag -a v1.1.0 -m "Version 1.1.0 release"
   git push origin v1.1.0
   ```

## Continuous Integration

### GitHub Actions for App Store

```yaml
name: Deploy to App Store

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'

      - name: Build iOS
        run: flutter build ios --release

      - name: Export Archive
        run: |
          # Export IPA (requires certificate setup)
          # Use Transporter to upload

      - name: Upload to App Store
        uses: Apple-Actions/upload-testflight-build@v1
        with:
          app-path: 'ios/Runner.ipa'
          issuer-id: ${{ secrets.APPSTORE_ISSUER_ID }}
          api-key-id: ${{ secrets.APPSTORE_API_KEY_ID }}
          api-private-key: ${{ secrets.APPSTORE_API_PRIVATE_KEY }}
```

---

**Last Updated**: 2026-06-09
**Bundle ID**: com.chargehero.customer
**Minimum iOS**: 12.0
**Target iOS**: 17.0+
