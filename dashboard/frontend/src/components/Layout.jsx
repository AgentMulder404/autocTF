import { Link, useLocation } from 'react-router-dom';
import { Shield, Target, Activity, AlertTriangle } from 'lucide-react';

export default function Layout({ children }) {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Activity },
    { path: '/targets', label: 'Targets', icon: Target },
    { path: '/scans', label: 'Scans', icon: Shield },
    { path: '/vulnerabilities', label: 'Vulnerabilities', icon: AlertTriangle },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-6">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-cyan-400" />
            <h1 className="text-xl font-bold">AutoCTF</h1>
          </div>
          <p className="text-sm text-gray-400 mt-1">Enterprise Dashboard</p>
        </div>

        <nav className="mt-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-6 py-3 transition-colors ${
                  isActive
                    ? 'bg-cyan-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
