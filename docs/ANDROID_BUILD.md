# 📱 Android APK Build Guide

## Option 1: PWA (Recommended — No Build Required)

The app is already configured as a Progressive Web App. Just:

1. Deploy the frontend to Vercel/Netlify/any host
2. Open the URL on Android Chrome
3. Tap "Install" when prompted → adds to home screen
4. Works like a native app (offline support, full screen)

```bash
# Deploy to Vercel
cd frontend
npx vercel --prod
```

## Option 2: EAS Build (Native APK)

For a real Android APK/AAB via Expo EAS:

### Prerequisites

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Install dependencies
cd frontend
npm install expo expo-build-properties
```

### Build APK (for testing)

```bash
cd frontend

# Build APK (sidesload on Android)
eas build --platform android --profile preview

# Build AAB (for Play Store)
eas build --platform android --profile production
```

### Build Process

1. EAS will ask to create a project — say yes
2. It uploads your code to Expo's cloud
3. Builds the APK/AAB (takes ~10-15 minutes)
4. Gives you a download link

### Install APK

```bash
# Download from the EAS link, then:
adb install ai-outreach.apk
```

## Option 3: Capacitor (Local Build)

For building locally without Expo cloud:

```bash
cd frontend

# Install Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/android

# Init Capacitor
npx cap init "AI Outreach" "com.aioutreach.app" --web-dir=out

# Build Next.js
npm run build

# Add Android platform
npx cap add android

# Sync web assets
npx cap sync

# Open in Android Studio
npx cap open android
```

Then in Android Studio: Build → Build APK.

---

## Quick Comparison

| Method | Speed | Effort | Result |
|--------|-------|--------|--------|
| **PWA** | Instant | Zero | Install from browser |
| **EAS Build** | 15 min | Low | Native APK/AAB |
| **Capacitor** | 30 min | Medium | Native APK + Android Studio |

**Recommendation**: Start with PWA. Only go native if you need push notifications or deep OS integration.
