import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, X, Calendar } from 'lucide-react';

export default function FilterBar({ page, filterOptions = {}, onApply }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({});
  const [expanded, setExpanded] = useState(false);

  // Initialize filters from URL params
  useEffect(() => {
    const initial = {};
    searchParams.forEach((value, key) => {
      initial[key] = value;
    });
    setFilters(initial);
  }, []);

  const filterConfigs = {
    sales: [
      { key: 'owner', label: 'Owner', options: filterOptions.owners || [] },
      { key: 'source', label: 'Source', options: filterOptions.sources || [] },
      { key: 'region', label: 'Region', options: filterOptions.regions || [] },
      { key: 'status', label: 'Status', options: filterOptions.statuses || [] },
    ],
    operations: [
      { key: 'team', label: 'Team', options: filterOptions.teams || [] },
      { key: 'service_type', label: 'Service Type', options: filterOptions.service_types || [] },
      { key: 'status', label: 'Status', options: filterOptions.statuses || [] },
      { key: 'client', label: 'Client', options: filterOptions.clients || [] },
    ],
  };

  const activeFilters = filterConfigs[page] || [];
  const hasFilters = Object.keys(filters).some((k) => filters[k]);

  const handleChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApply = () => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params[k] = v;
    });
    setSearchParams(params);
    onApply?.(params);
  };

  const handleClear = () => {
    setFilters({});
    setSearchParams({});
    onApply?.({});
  };

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
      <div className="px-6 py-3">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <Filter size={14} />
            Filters
            {hasFilters && (
              <span className="bg-blue-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
                {Object.values(filters).filter(Boolean).length}
              </span>
            )}
          </button>

          {/* Date range - always visible */}
          <div className="flex items-center gap-2">
            <Calendar size={14} className="text-slate-400" />
            <input
              type="date"
              value={filters.date_from || filters.start_date || ''}
              onChange={(e) => {
                handleChange('date_from', e.target.value);
                handleChange('start_date', e.target.value);
              }}
              className="px-2 py-1 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              placeholder="Start Date"
            />
            <span className="text-slate-400 text-xs">to</span>
            <input
              type="date"
              value={filters.date_to || filters.end_date || ''}
              onChange={(e) => {
                handleChange('date_to', e.target.value);
                handleChange('end_date', e.target.value);
              }}
              className="px-2 py-1 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <button
            onClick={handleApply}
            className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply
          </button>
          {hasFilters && (
            <button
              onClick={handleClear}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-red-600 transition-colors"
            >
              <X size={14} />
              Clear
            </button>
          )}
        </div>

        {expanded && activeFilters.length > 0 && (
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            {activeFilters.map((f) => (
              <select
                key={f.key}
                value={filters[f.key] || ''}
                onChange={(e) => handleChange(f.key, e.target.value)}
                className="px-3 py-1.5 text-sm border border-slate-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 min-w-[140px]"
              >
                <option value="">{f.label} (All)</option>
                {f.options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
