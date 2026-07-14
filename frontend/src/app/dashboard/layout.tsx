'use client';

import { useState, useEffect, createContext, useContext } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { api } from '@/lib/api';

// Auth context
const AuthContext = createContext<{ user: any; loading: boolean; logout: () => void }>({
  user: null, loading: true, logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/leads', label: 'Leads', icon: '👥' },
  { href: '/campaigns', label: 'Campaigns', icon: '📧' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    api.getMe()
      .then(setUser)
      .catch(() => router.push('/auth/login'))
      .finally(() => setLoading(false));
  }, []);

  const logout = () => {
    api.clearToken();
    router.push('/auth/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      <div className="min-h-screen flex">
        {/* Sidebar */}
        <aside className={`bg-gray-900 text-white ${sidebarOpen ? 'w-64' : 'w-20'} transition-all duration-300 flex flex-col`}>
          <div className="p-4 flex items-center justify-between border-b border-gray-700">
            {sidebarOpen && <h1 className="text-xl font-bold">🚀 AI Outreach</h1>}
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-gray-400 hover:text-white">
              {sidebarOpen ? '←' : '→'}
            </button>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  pathname.startsWith(item.href)
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                {sidebarOpen && <span className="font-medium">{item.label}</span>}
              </Link>
            ))}
          </nav>

          <div className="p-4 border-t border-gray-700">
            <div className={`flex items-center ${sidebarOpen ? 'gap-3' : 'justify-center'}`}>
              <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-sm font-bold">
                {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || '?'}
              </div>
              {sidebarOpen && (
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user?.full_name || user?.email}</p>
                  <p className="text-xs text-gray-400 truncate">{user?.plan} plan</p>
                </div>
              )}
            </div>
            {sidebarOpen && (
              <button onClick={logout} className="mt-3 w-full text-left text-sm text-gray-400 hover:text-white px-3 py-1.5 rounded hover:bg-gray-800">
                Sign out
              </button>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <div className="p-6 max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </AuthContext.Provider>
  );
}
