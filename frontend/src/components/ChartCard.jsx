export default function ChartCard({ title, subtitle, children, footer, loading = false, className = '' }) {
  if (loading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-5 animate-pulse ${className}`}>
        <div className="h-5 bg-slate-200 rounded w-40 mb-2" />
        <div className="h-3 bg-slate-200 rounded w-24 mb-6" />
        <div className="h-64 bg-slate-100 rounded-lg" />
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-5 hover:shadow-md transition-shadow duration-200 ${className}`}>
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="w-full">{children}</div>
      {footer && <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">{footer}</div>}
    </div>
  );
}
