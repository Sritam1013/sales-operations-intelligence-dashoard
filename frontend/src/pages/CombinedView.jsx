import { useState, useEffect } from 'react';
import { GitMerge, Building2, DollarSign, AlertCircle } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import { getSalesToOps } from '../api';
import { formatCurrency, formatNumber } from '../utils';

export default function CombinedView() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await getSalesToOps();
        setData(res.data);
      } catch (err) {
        console.error('Error fetching combined data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Compute summary
  const summary = data.reduce(
    (acc, company) => {
      acc.matchedCompanies++;
      acc.totalCrmLeads += company.crm_leads?.length || 0;
      acc.totalOpsProjects += company.operations_projects?.length || 0;
      acc.totalDealValue += (company.crm_leads || []).reduce((s, l) => s + (l.deal_value || 0), 0);
      acc.totalProjectValue += (company.operations_projects || []).reduce((s, p) => s + (p.budget || 0), 0);
      return acc;
    },
    { matchedCompanies: 0, totalCrmLeads: 0, totalOpsProjects: 0, totalDealValue: 0, totalProjectValue: 0 }
  );

  const tableData = data.map((company) => ({
    company: company.company,
    crm_leads: company.crm_leads?.length || 0,
    total_deal_value: (company.crm_leads || []).reduce((s, l) => s + (l.deal_value || 0), 0),
    ops_projects: company.operations_projects?.length || 0,
    total_project_value: (company.operations_projects || []).reduce((s, p) => s + (p.budget || 0), 0),
    combined_value: (company.crm_leads || []).reduce((s, l) => s + (l.deal_value || 0), 0) + (company.operations_projects || []).reduce((s, p) => s + (p.budget || 0), 0),
    stages: [...new Set((company.crm_leads || []).map((l) => l.stage).filter(Boolean))].join(', '),
    statuses: [...new Set((company.operations_projects || []).map((p) => p.status).filter(Boolean))].join(', '),
  }));

  const columns = [
    { key: 'company', label: 'Company' },
    { key: 'crm_leads', label: 'CRM Leads', render: (v) => <span className="font-medium text-blue-600">{v}</span> },
    { key: 'total_deal_value', label: 'Deal Value', render: (v) => formatCurrency(v) },
    { key: 'ops_projects', label: 'Ops Projects', render: (v) => <span className="font-medium text-purple-600">{v}</span> },
    { key: 'total_project_value', label: 'Project Value', render: (v) => formatCurrency(v) },
    { key: 'combined_value', label: 'Combined', render: (v) => <span className="font-bold text-emerald-700">{formatCurrency(v)}</span> },
    { key: 'stages', label: 'CRM Stages' },
    { key: 'statuses', label: 'Ops Status' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Combined Sales-to-Operations View</h2>
        <p className="text-sm text-slate-500 mt-1">Companies appearing in both CRM and Operations data, matched by company name</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Matched Companies" value={formatNumber(summary.matchedCompanies)} icon={Building2} color="blue" loading={loading} />
        <KpiCard title="Total CRM Leads" value={formatNumber(summary.totalCrmLeads)} icon={GitMerge} color="green" loading={loading} subtitle="Across matched companies" />
        <KpiCard title="Total Deal Value" value={formatCurrency(summary.totalDealValue)} icon={DollarSign} color="purple" loading={loading} />
        <KpiCard title="Total Project Value" value={formatCurrency(summary.totalProjectValue)} icon={DollarSign} color="amber" loading={loading} />
      </div>

      {/* Table */}
      <DataTable
        title="Cross-Source Company Matches"
        columns={columns}
        data={tableData}
        loading={loading}
        pageSize={15}
        emptyMessage="No matched companies found. Click 'Refresh Data' to load data first."
      />
    </div>
  );
}
