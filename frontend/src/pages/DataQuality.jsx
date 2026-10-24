import { useState, useEffect } from 'react';
import { Database, AlertTriangle, Copy, Unlink } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import { getDataQualitySummary, getDataQualityUnmatched, getDataStatus } from '../api';
import { formatNumber } from '../utils';

export default function DataQuality() {
  const [summary, setSummary] = useState(null);
  const [unmatched, setUnmatched] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [sRes, uRes, stRes] = await Promise.all([
          getDataQualitySummary(),
          getDataQualityUnmatched(),
          getDataStatus(),
        ]);
        setSummary(sRes.data);
        setUnmatched(uRes.data);
        setStatus(stRes.data);
      } catch (err) {
        console.error('Error fetching data quality:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalMissing = summary
    ? Object.values(summary.crm_missing || {}).reduce((s, v) => s + v, 0)
      + Object.values(summary.ops_missing || {}).reduce((s, v) => s + v, 0)
      + Object.values(summary.targets_missing || {}).reduce((s, v) => s + v, 0)
    : 0;

  const totalDuplicates = summary
    ? (summary.crm_duplicates || 0) + (summary.ops_duplicates || 0) + (summary.targets_duplicates || 0)
    : 0;

  const totalRecords = status?.record_counts
    ? Object.values(status.record_counts).reduce((s, v) => s + v, 0)
    : 0;

  const unmatchedColumns = [
    { key: 'source', label: 'Source', render: (v) => (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        v === 'crm_leads' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
      }`}>{v}</span>
    )},
    { key: 'company', label: 'Company Name' },
  ];

  // Build missing values table
  const missingData = [];
  if (summary) {
    Object.entries(summary.crm_missing || {}).forEach(([field, count]) => {
      missingData.push({ source: 'CRM Leads', field, count });
    });
    Object.entries(summary.ops_missing || {}).forEach(([field, count]) => {
      missingData.push({ source: 'Operations', field, count });
    });
    Object.entries(summary.targets_missing || {}).forEach(([field, count]) => {
      missingData.push({ source: 'Targets', field, count });
    });
  }

  const missingColumns = [
    { key: 'source', label: 'Data Source', render: (v) => (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        v === 'CRM Leads' ? 'bg-blue-100 text-blue-700' :
        v === 'Operations' ? 'bg-purple-100 text-purple-700' :
        'bg-amber-100 text-amber-700'
      }`}>{v}</span>
    )},
    { key: 'field', label: 'Field' },
    { key: 'count', label: 'Missing Count', render: (v) => <span className="font-medium text-red-600">{formatNumber(v)}</span> },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Data Quality Report</h2>
        <p className="text-sm text-slate-500 mt-1">
          {status?.last_loaded_at
            ? `Data loaded: ${new Date(status.last_loaded_at).toLocaleString()}`
            : 'No data loaded yet — click Refresh Data'}
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Total Records" value={formatNumber(totalRecords)} icon={Database} color="blue" loading={loading}
          subtitle={status?.record_counts ? `CRM: ${status.record_counts.crm_leads || 0} | Ops: ${status.record_counts.operations_projects || 0} | Targets: ${status.record_counts.targets_forecasts || 0}` : ''}
        />
        <KpiCard title="Missing Values" value={formatNumber(totalMissing)} icon={AlertTriangle} color={totalMissing > 50 ? 'red' : 'amber'} loading={loading} />
        <KpiCard title="Duplicates Found" value={formatNumber(totalDuplicates)} icon={Copy} color="purple" loading={loading}
          subtitle={summary ? `CRM: ${summary.crm_duplicates} | Ops: ${summary.ops_duplicates} | Targets: ${summary.targets_duplicates}` : ''}
        />
        <KpiCard title="Unmatched Companies" value={formatNumber((summary?.unmatched_crm_companies || 0) + (summary?.unmatched_ops_companies || 0))} icon={Unlink} color="amber" loading={loading}
          subtitle={summary ? `CRM-only: ${summary.unmatched_crm_companies} | Ops-only: ${summary.unmatched_ops_companies}` : ''}
        />
      </div>

      {/* Record Counts Card */}
      {status?.record_counts && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-base font-semibold text-slate-800 mb-3">Record Counts by Source</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(status.record_counts).map(([source, count]) => (
              <div key={source} className="p-3 bg-slate-50 rounded-lg text-center">
                <p className="text-xs text-slate-500 uppercase tracking-wide">{source.replace(/_/g, ' ')}</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">{formatNumber(count)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Values Table */}
      <DataTable
        title="Missing Values by Field"
        columns={missingColumns}
        data={missingData}
        loading={loading}
        pageSize={20}
        emptyMessage="No missing values detected"
      />

      {/* Unmatched Companies */}
      <DataTable
        title="Unmatched Companies"
        columns={unmatchedColumns}
        data={unmatched}
        loading={loading}
        collapsible
        defaultCollapsed={false}
        pageSize={15}
        emptyMessage="All companies are matched across sources"
      />
    </div>
  );
}
