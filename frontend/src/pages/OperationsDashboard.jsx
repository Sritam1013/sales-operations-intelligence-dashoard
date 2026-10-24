import { useState, useEffect, useCallback } from 'react';
import { Briefcase, AlertTriangle, CheckCircle, Clock, ShieldCheck } from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import KpiCard from '../components/KpiCard';
import ChartCard from '../components/ChartCard';
import FilterBar from '../components/FilterBar';
import DataTable from '../components/DataTable';
import {
  getOpsKpis, getProjectsByStatus, getProjectsOverTime,
  getWorkloadByTeam, getWorkloadByService, getSlaOverview,
  getTargetsVsActuals, getOverdueProjects, getFilterOptions,
} from '../api';
import { COLORS, formatCurrency, formatNumber, formatPercent } from '../utils';

const SLA_COLORS = { 'Within SLA': '#10B981', 'At Risk': '#F59E0B', 'Breached': '#EF4444' };
const STATUS_COLORS = { 'Open': '#3B82F6', 'In Progress': '#8B5CF6', 'Completed': '#10B981', 'Overdue': '#EF4444', 'On Hold': '#F59E0B', 'Cancelled': '#6B7280' };

export default function OperationsDashboard() {
  const [filters, setFilters] = useState({});
  const [filterOptions, setFilterOptions] = useState({});
  const [kpis, setKpis] = useState(null);
  const [byStatus, setByStatus] = useState([]);
  const [overTime, setOverTime] = useState([]);
  const [byTeam, setByTeam] = useState([]);
  const [byService, setByService] = useState([]);
  const [sla, setSla] = useState([]);
  const [targets, setTargets] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const [kRes, sRes, tRes, tmRes, svRes, slRes, tvRes, odRes, fRes] = await Promise.all([
        getOpsKpis(params),
        getProjectsByStatus(params),
        getProjectsOverTime(params),
        getWorkloadByTeam(params),
        getWorkloadByService(params),
        getSlaOverview(params),
        getTargetsVsActuals(params),
        getOverdueProjects(params),
        getFilterOptions(),
      ]);
      setKpis(kRes.data);
      setByStatus(sRes.data);
      setOverTime(tRes.data);
      setByTeam(tmRes.data);
      setByService(svRes.data);
      setSla(slRes.data);
      setTargets(tvRes.data);
      setOverdue(odRes.data);
      setFilterOptions(fRes.data);
    } catch (err) {
      console.error('Error fetching ops data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  const handleFilter = (params) => { setFilters(params); fetchAll(params); };

  // Aggregate targets by period
  const targetsByPeriod = targets.reduce((acc, t) => {
    const existing = acc.find((a) => a.period === t.period);
    if (existing) {
      existing.target_revenue += t.target_revenue;
      existing.actual_revenue += t.actual_revenue;
    } else {
      acc.push({ period: t.period, target_revenue: t.target_revenue, actual_revenue: t.actual_revenue });
    }
    return acc;
  }, []).sort((a, b) => a.period.localeCompare(b.period));

  const overdueColumns = [
    { key: 'project_id', label: 'Project ID' },
    { key: 'project_name', label: 'Name' },
    { key: 'client_company', label: 'Client' },
    { key: 'assigned_team', label: 'Team' },
    { key: 'service_type', label: 'Service' },
    { key: 'deadline', label: 'Deadline' },
    { key: 'budget', label: 'Budget', render: (v) => formatCurrency(v) },
    { key: 'priority', label: 'Priority', render: (v) => (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        v === 'Critical' ? 'bg-red-100 text-red-700' :
        v === 'High' ? 'bg-amber-100 text-amber-700' :
        v === 'Medium' ? 'bg-blue-100 text-blue-700' :
        'bg-slate-100 text-slate-700'
      }`}>{v}</span>
    )},
  ];

  const slaCompliance = kpis?.sla_compliance_pct || 0;
  const slaColor = slaCompliance >= 90 ? 'green' : slaCompliance >= 75 ? 'amber' : 'red';
  const overdueRate = kpis?.total_projects > 0 ? (kpis.overdue_projects / kpis.total_projects * 100) : 0;

  return (
    <div>
      <FilterBar page="operations" filterOptions={filterOptions} onApply={handleFilter} />

      <div className="p-6 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard title="Total Projects" value={formatNumber(kpis?.total_projects)} icon={Briefcase} color="blue" loading={loading} />
          <KpiCard title="Open Projects" value={formatNumber(kpis?.open_projects)} icon={Clock} color="purple" loading={loading} />
          <KpiCard title="Overdue" value={formatNumber(kpis?.overdue_projects)} icon={AlertTriangle} color={overdueRate > 10 ? 'red' : 'amber'} loading={loading} subtitle={`${overdueRate.toFixed(1)}% of total`} />
          <KpiCard title="SLA Compliance" value={formatPercent(slaCompliance)} icon={ShieldCheck} color={slaColor} loading={loading} />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Projects by Status" subtitle="Current status distribution" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={byStatus} dataKey="count" nameKey="category" cx="50%" cy="50%" innerRadius={60} outerRadius={100} label={({ category, count }) => `${category} (${count})`}>
                  {byStatus.map((entry, i) => <Cell key={i} fill={STATUS_COLORS[entry.category] || COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Projects Over Time" subtitle="Monthly new projects" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={overTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#8B5CF6" strokeWidth={2} dot={{ fill: '#8B5CF6' }} name="Projects" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Workload by Team" subtitle="Projects assigned per team" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byTeam}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => name === 'Budget' ? formatCurrency(v) : v} />
                <Legend />
                <Bar dataKey="count" fill="#3B82F6" name="Projects" radius={[4, 4, 0, 0]} />
                <Bar dataKey="value" fill="#10B981" name="Budget" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="SLA Overview" subtitle="SLA status breakdown" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={sla} dataKey="count" nameKey="category" cx="50%" cy="50%" innerRadius={60} outerRadius={100} label={({ category, count }) => `${category} (${count})`}>
                  {sla.map((entry, i) => <Cell key={i} fill={SLA_COLORS[entry.category] || COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Workload by Service Type */}
        <ChartCard title="Workload by Service Type" subtitle="Project distribution by service" loading={loading}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byService} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="category" type="category" width={130} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#F59E0B" name="Projects" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Targets vs Actuals */}
        <ChartCard title="Targets vs Actuals" subtitle="Monthly revenue target achievement" loading={loading}>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={targetsByPeriod}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="period" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(v) => formatCurrency(v)} />
              <Legend />
              <Bar dataKey="target_revenue" fill="#94A3B8" name="Target" radius={[4, 4, 0, 0]} />
              <Bar dataKey="actual_revenue" fill="#3B82F6" name="Actual" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Overdue Projects Table */}
        <DataTable
          title={`🚨 Overdue Projects (${overdue.length})`}
          columns={overdueColumns}
          data={overdue}
          collapsible
          defaultCollapsed={false}
          loading={loading}
          emptyMessage="No overdue projects"
        />
      </div>
    </div>
  );
}
