# ChargeHero Customer App - Android Deployment to Google Play

## Prerequisites

- Android Studio installed
- Flutter SDK 3.16.0+
- JDK 11+ installed
- Google Play Developer account ($25 one-time fee)
- Google Play Console access
- Signing certificate and keystore file
- App version properly configured

## App Signing Setup

### Generate Signing Keystore

```bash
keytool -genkey -v -keystore ~/chargehero-release.jks \
  -keyalg RSA -keysize 2048 -validity 10950 \
  -alias chargehero_key
```

Store the keystore password securely. You'll need it for signing.

### Configure Keystore in Gradle

1. Place keystore file in project:
```bash
cp ~/chargehero-release.jks android/app/chargehero-release.jks
```

2. Edit `android/key.properties`:
```properties
storePassword=your-keystore-password
keyPassword=your-key-password
keyAlias=chargehero_key
storeFile=chargehero-release.jks
```

3. Update `android/app/build.gradle`:

```gradle
android {
    // ... other config

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile file(keystoreProperties['storeFile'])
            storePassword keystoreProperties['storePassword']
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

## Build Release APK/AAB

### Build App Bundle (AAB - Recommended)

```bash
cd chargehero_customer_app

# Build release app bundle
flutter build appbundle \
  --release \
  --target-platform=android-arm64,android-arm,android-x86,android-x86_64

# Or using gradle directly
cd android
./gradlew bundleRelease
cd ..
```

Output: `build/app/outputs/bundle/release/app-release.aab`

### Build APK (Alternative)

```bash
flutter build apk --release
```

Output: `build/app/outputs/apk/release/app-release.apk`

## Google Play Console Setup

### 1. Create App

1. Go to [Google Play Console](https://play.google.com/console)
2. Click "Create new app"
3. App name: "ChargeHero"
4. Default language: English
5. Category: "Tools"
6. Content rating: "Everyone"

### 2. Add Release

1. Navigate to "Release" > "Production"
2. Click "Create new release"
3. Upload AAB file
4. Accept default rollout percentage (100% for initial release)

### 3. Configure App Details

#### Store Listing
- Title: "ChargeHero - EV Charger Support"
- Short description: "24/7 support for EV charging issues"
- Full description:
  ```
  ChargeHero provides instant support for EV charger problems.
  
  Features:
  - Real-time engineer dispatch
  - Live tracking of support engineers
  - Instant troubleshooting assistance
  - Service report and rating system
  
  Service available in India.
  ```
- Screenshots: Add 5-8 screenshots (1440x2560px)
- Feature graphic: 1024x500px
- Icon: 512x512px (high resolution icon)

#### Pricing & Distribution
- Price: Free
- Countries: Select India
- Content rating questionnaire: Fill out
- Target audience: 18+ (for location services)

#### Privacy & Permissions
- Privacy policy: https://chargehero.com/privacy
- Terms of service: https://chargehero.com/terms

### 4. Content Rating

Answer the content rating questionnaire:
- Violence: None
- Sexual content: None
- Profanity: None
- Location: Yes (GPS tracking)
- Personal information: Yes (phone, name)

## Testing Before Release

### Pre-Release Testing

1. Install signed APK on multiple devices:
```bash
flutter install --release
```

2. Test all user flows:
   - Registration and OTP verification
   - Charger registration
   - Ticket creation
   - Engineer tracking
   - Checklist approval
   - Service rating

3. Test on multiple Android versions:
   - Android 8 (API 26)
   - Android 10 (API 29)
   - Android 12 (API 31)
   - Android 13 (API 33)
   - Android 14 (API 34)

4. Test on different device sizes:
   - Small (4.5" phones)
   - Medium (5.5" phones)
   - Large (6.5"+ tablets)

### Beta Testing (Optional but Recommended)

1. Create closed beta release
2. Add beta testers (1-100 users)
3. Gather feedback
4. Fix issues
5. Promote to production

## Release Process

### Step-by-Step Release

1. **Increment version number**:
```yaml
# pubspec.yaml
version: 1.0.0+1  # major.minor.patch+build
```

2. **Build AAB**:
```bash
flutter build appbundle --release
```

3. **Upload to Play Console**:
   - Go to Release > Production
   - Click "Create new release"
   - Upload AAB file
   - Set rollout: 5% (staged rollout)

4. **Monitor for crashes**:
   - Play Console shows crash rates
   - Wait 12 hours
   - Check for ANR (Application Not Responding) rates

5. **Increase rollout** (if no issues):
   - 12h: 5% → 25%
   - 24h: 25% → 50%
   - 48h: 50% → 100%

6. **Track metrics**:
   - Crash rate (target: <0.1%)
   - ANR rate (target: <0.05%)
   - Rating (target: >4.5 stars)
   - Reviews: Address user feedback

## Staged Rollout Strategy

First release:
- Day 1: 5% rollout
- Day 1-2: Monitor crashes/ANRs
- Day 2: 25% if healthy
- Day 3: 50% if healthy
- Day 4: 100% if healthy

Subsequent releases:
- Can go 100% if confident
- Always monitor first 24 hours

## Post-Release Monitoring

### Key Metrics

1. **Crashes and ANRs**
   - Target: <0.1% crash rate
   - Target: <0.05% ANR rate
   - Action: Hotfix if above thresholds

2. **User Ratings**
   - Target: >4.5 stars
   - Action: Respond to critical reviews

3. **Performance**
   - App size: <50MB (download size)
   - Startup time: <2 seconds
   - Memory: <250MB

4. **Downloads**
   - Track daily active users
   - Monitor retention (day-1, day-7, day-30)
   - Compare to baseline

### Responding to Issues

**Critical Crash (>1% rate)**
```
1. Identify crash in Android Vitals
2. Debug locally, reproduce issue
3. Fix code
4. Increment version
5. Build and upload hotfix AAB
6. Release with 50% rollout
7. Monitor for 24 hours
8. Increase to 100%
```

**Negative Reviews**
```
1. Reply to review professionally
2. Offer alternative solutions
3. Request user contact via support
4. Follow up with fix if applicable
```

## Troubleshooting

### AAB Upload Fails

```
Error: "It looks like you haven't uploaded an APK or Android App Bundle yet"
Solution: Ensure AAB is properly signed and correct format
```

### App Crashes on Launch

```
Error: "Unfortunately, ChargeHero has stopped"
Solution: 
1. Check logcat: flutter logs
2. Verify all permissions in AndroidManifest.xml
3. Check API compatibility
4. Test on different Android versions
```

### Network Errors

```
Error: "Failed to connect to API"
Solution:
1. Verify API_BASE_URL in config.dart matches production
2. Check CORS configuration
3. Verify SSL certificate
4. Test with curl from device
```

## Security Considerations

### App Signing
- Use **v2 scheme** signing (modern, more secure)
- Store keystore password securely (not in code)
- Keep keystore backup in secure location

### Certificate Pinning
Implement certificate pinning to prevent MITM attacks:

```dart
// lib/config.dart
import 'package:http/http.dart' as http;

class PinnedHttpClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    // Implement certificate pinning
    // Verify server certificate matches pinned cert
  }
}
```

### Permissions
Request minimum required permissions:
- Location (FINE_LOCATION)
- Phone (READ_PHONE_STATE)
- Calendar (for notifications - optional)

Avoid requesting unnecessary permissions.

## Release Notes Template

When releasing new version, include:

```
### Version 1.1.0 - 2026-06-15

**New Features**
- Added push notifications for job updates
- Improved engineer tracking with better ETA

**Bug Fixes**
- Fixed crash when internet disconnected
- Fixed ticket list not updating in real-time

**Improvements**
- Faster app startup time
- Better offline support

**Technical**
- Updated dependencies
- Improved code security
- Optimized database queries

**Known Issues**
- None reported
```

## Version Management

### Versioning Scheme

```
major.minor.patch+build

Examples:
1.0.0+1   (initial release)
1.1.0+2   (minor feature addition)
1.1.1+3   (bug fix)
2.0.0+4   (major release)
```

### Version History

Maintain version history for reference:

| Version | Release Date | Notes |
|---------|-------------|-------|
| 1.0.0 | 2026-06-09 | Initial release |
| 1.1.0 | 2026-06-30 | Notifications |
| 1.1.1 | 2026-07-05 | Bug fixes |

## Continuous Deployment

### GitHub Actions for Play Store

```yaml
name: Deploy to Play Store

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'

      - name: Build AAB
        run: flutter build appbundle --release

      - name: Upload to Play Store
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_KEY }}
          packageName: com.chargehero.customer
          releaseFiles: 'build/app/outputs/bundle/release/app-release.aab'
          track: internal
          status: draft
```

## Support

- **Issues**: Create GitHub issue
- **Crash Reports**: Monitor Play Console Crashes & ANRs
- **User Feedback**: Respond to Play Store reviews
- **Analytics**: Use Google Analytics in app

---

**Last Updated**: 2026-06-09
**App ID**: com.chargehero.customer
**Minimum Android**: API 26 (Android 8)
**Target Android**: API 34 (Android 14)
