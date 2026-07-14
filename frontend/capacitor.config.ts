import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.aioutreach.app',
  appName: 'AI Outreach',
  webDir: 'out',
  server: {
    androidScheme: 'https',
    url: 'https://ai-outreach.vercel.app',
    cleartext: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#2563eb',
      showSpinner: true,
      spinnerColor: '#ffffff',
    },
    StatusBar: {
      style: 'LIGHT',
      backgroundColor: '#2563eb',
    },
  },
  android: {
    allowMixedContent: true,
    backgroundColor: '#2563eb',
  },
};

export default config;
