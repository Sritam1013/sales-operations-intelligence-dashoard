import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { BarChart3, Briefcase, GitMerge, ShieldCheck, Lightbulb, RefreshCw, Menu, X, Database } from 'lucide-react';
import { loadData, getDataStatus } from '../api';

const navItems = [
  { to: '/sales', label: 'Sales Dashboard', icon: BarChart3 },
  { to: '/operations', label: 'Operations', icon: Briefcase },
  { to: '/combined', label: 'Combined View', icon: GitMerge },
  { to: '/data-quality', label: 'Data Quality', icon: ShieldCheck },
  { to: '/insights', label: 'AI Insights', icon: Lightbulb },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastLoad, setLastLoad] = useState(null);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await loadData();
      const res = await getDataStatus();
      setLastLoad(res.data.last_loaded_at);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white transform transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 flex flex-col`}>
        <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-700">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Database size={20} />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wide">Sales & Ops</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest">Intelligence</p>
          </div>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Prototype</p>
          <p className="text-xs text-slate-400">Braahmam International</p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-slate-200 px-4 lg:px-6 py-3 flex items-center justify-between shadow-sm shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-1.5 rounded-md hover:bg-slate-100">
              <Menu size={20} />
            </button>
            <h2 className="text-lg font-semibold text-slate-800 hidden sm:block">Sales & Operations Intelligence Dashboard</h2>
          </div>
          <div className="flex items-center gap-3">
            {lastLoad && (
              <span className="text-xs text-slate-500 hidden md:block">
                Last loaded: {new Date(lastLoad).toLocaleString()}
              </span>
            )}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Loading...' : 'Refresh Data'}
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-slate-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
