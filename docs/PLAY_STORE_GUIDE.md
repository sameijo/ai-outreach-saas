# 📱 Google Play Store — Complete Submission Guide

## Step 1: Create Play Store Developer Account

1. Go to **https://play.google.com/console**
2. Pay **$25 one-time fee**
3. Complete identity verification

## Step 2: Build APK/AAB

### Option A: EAS Build (Recommended)

```bash
cd frontend

# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Build AAB for Play Store
eas build --platform android --profile production

# Download the .aab file from the link
```

### Option B: Local Build with Capacitor

```bash
cd frontend

# Install
npm install @capacitor/core @capacitor/cli @capacitor/android

# Init
npx cap init "AI Outreach" "com.aioutreach.app" --web-dir=out

# Build Next.js
npm run build

# Add Android
npx cap add android
npx cap sync

# Open Android Studio
npx cap open android

# In Android Studio:
# Build → Generate Signed Bundle/APK → Android App Bundle
```

## Step 3: Create Store Listing

### App Name
```
AI Outreach — Email Lead Generator
```

### Short Description (80 chars max)
```
AI-powered cold email outreach, lead generation & campaign automation
```

### Full Description (4000 chars max)
```
🚀 AI Outreach — The All-in-One Email Lead Generation Platform

Find verified business leads, personalize with AI, send bulk email campaigns, and track everything — all from your phone.

✨ KEY FEATURES

📧 Lead Discovery
• Search leads by industry, location, job title
• Import from CSV files
• Email verification to reduce bounces
• Apollo.io & Hunter.io integration

🤖 AI Personalization
• AI writes unique intro for each lead
• Scrapes company websites for context
• Professional, casual, or persuasive tones
• "Hi John, congrats on Acme's Series B!" style

📬 Email Campaigns
• Send via SendGrid, Amazon SES, Mailgun, Resend
• Follow-up sequences (drip campaigns)
• Rate limiting & send windows
• Open, click & reply tracking

📊 Dashboard & Analytics
• Real-time campaign performance
• Open rate, click rate, reply rate charts
• Export data to CSV

🔥 Email Warm-up
• 14-day automatic warm-up schedule
• Builds sender reputation gradually
• Avoids spam folders

🧪 A/B Testing
• Test multiple subject lines
• Auto-select winning variant
• Data-driven optimization

💳 Flexible Plans
• Free: 100 credits
• Starter: 2,000 credits ($49/mo)
• Pro: 10,000 credits ($149/mo)
• Enterprise: 50,000 credits ($499/mo)

🔒 SECURE & COMPLIANT
• CAN-SPAM compliant
• GDPR compliant
• Automatic unsubscribe links
• Encrypted data storage

Perfect for:
• Sales teams
• Marketing agencies
• Startups & founders
• Recruiters
• Business development

Start generating leads today! 🚀
```

### Category
```
Business
```

### Content Rating
```
Everyone
```

### Privacy Policy URL
```
https://yourdomain.com/privacy
```

## Step 4: Store Assets

### App Icon (512x512 PNG)
Already generated: `frontend/public/icons/icon-512.png`

### Feature Graphic (1024x500 PNG)
Create in Canva or use this template:
- Background: #2563eb (blue gradient)
- Logo centered
- Text: "AI Outreach — Email Lead Generation"

### Screenshots (minimum 2)
Take screenshots of:
1. Dashboard page
2. Leads page
3. Campaigns page
4. Settings page

**How to take screenshots:**
```bash
# Run the app
cd frontend && npm run dev

# Open in browser, take screenshots at 1080x1920 resolution
# Use Chrome DevTools → Toggle Device Toolbar → Pixel 5
```

## Step 5: Upload & Submit

1. Go to **Google Play Console**
2. Click **Create App**
3. Fill in all the details above
4. Upload AAB/APK under **Release → Production**
5. Upload screenshots and graphics
6. Set pricing (Free)
7. Complete content rating questionnaire
8. Submit for review

**Review time:** Usually 3-7 days

## Step 6: After Approval

Your app will be live at:
```
https://play.google.com/store/apps/details?id=com.aioutreach.app
```

Share link:
```
https://play.google.com/store/apps/details?id=com.aioutreach.app
```

---

## 🍎 Apple App Store (Bonus)

For iOS later:
1. Apple Developer Account: **$99/year**
2. Use same EAS build: `eas build --platform ios`
3. Submit via App Store Connect
4. Review time: 1-3 days

---

## 📋 Checklist Before Submitting

- [ ] App icon (512x512) ✅
- [ ] Feature graphic (1024x500)
- [ ] Screenshots (min 2, recommended 4-8)
- [ ] Privacy policy URL
- [ ] App description
- [ ] Content rating completed
- [ ] AAB/APK built and signed
- [ ] Test on real device
