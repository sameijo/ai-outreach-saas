'use client';

import { useState, useEffect } from 'react';

export default function PWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(console.error);
    }

    // Listen for install prompt
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShowInstall(false);
    }
    setDeferredPrompt(null);
  };

  if (!showInstall) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-primary-600 text-white rounded-xl p-4 shadow-lg flex items-center gap-3 z-50">
      <div>
        <p className="font-semibold">Install AI Outreach</p>
        <p className="text-sm text-primary-100">Add to home screen for app experience</p>
      </div>
      <button onClick={handleInstall} className="bg-white text-primary-600 px-4 py-2 rounded-lg font-medium hover:bg-primary-50">
        Install
      </button>
      <button onClick={() => setShowInstall(false)} className="text-primary-200 hover:text-white">
        ✕
      </button>
    </div>
  );
}
