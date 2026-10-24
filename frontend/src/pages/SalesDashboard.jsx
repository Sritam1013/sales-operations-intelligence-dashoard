import { useState, useEffect, useCallback } from 'react';
import { Users, DollarSign, TrendingUp, Target, AlertTriangle } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import KpiCard from '../components/KpiCard';
import ChartCard from '../components/ChartCard';
import FilterBar from '../components/FilterBar';
import DataTable from '../components/DataTable';
import {
  getSalesKpis, getLeadsOverTime, getLeadsBySource,
  getLeadsByStage, getLeadsByOwner, getLeadsByRegion,
  getStaleLeads, getFilterOptions,
} from '../api';
import { COLORS, formatCurrency, formatNumber } from '../utils';

export default function SalesDashboard() {
  const [filters, setFilters] = useState({});
  const [filterOptions, setFilterOptions] = useState({});
  const [kpis, setKpis] = useState(null);
  const [leadsTime, setLeadsTime] = useState([]);
  const [bySource, setBySource] = useState([]);
  const [byStage, setByStage] = useState([]);
  const [byOwner, setByOwner] = useState([]);
  const [byRegion, setByRegion] = useState([]);
  const [stale, setStale] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async (params = {}) => {
    setLoading(true);
    try {
      const [kRes, tRes, sRes, stRes, oRes, rRes, slRes, fRes] = await Promise.all([
        getSalesKpis(params),
        getLeadsOverTime(params),
        getLeadsBySource(params),
        getLeadsByStage(params),
        getLeadsByOwner(params),
        getLeadsByRegion(params),
        getStaleLeads(params),
        getFilterOptions(),
      ]);
      setKpis(kRes.data);
      setLeadsTime(tRes.data);
      setBySource(sRes.data);
      setByStage(stRes.data);
      setByOwner(oRes.data);
      setByRegion(rRes.data);
      setStale(slRes.data);
      setFilterOptions(fRes.data);
    } catch (err) {
      console.error('Error fetching sales data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleFilter = (params) => {
    setFilters(params);
    fetchAll(params);
  };

  const staleColumns = [
    { key: 'lead_id', label: 'Lead ID' },
    { key: 'contact_name', label: 'Contact' },
    { key: 'company', label: 'Company' },
    { key: 'owner', label: 'Owner' },
    { key: 'stage', label: 'Stage' },
    { key: 'deal_value', label: 'Deal Value', render: (v) => formatCurrency(v) },
    { key: 'last_activity', label: 'Last Activity' },
  ];

  return (
    <div>
      <FilterBar page="sales" filterOptions={filterOptions} onApply={handleFilter} />

      <div className="p-6 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard title="Total Leads" value={formatNumber(kpis?.total_leads)} icon={Users} color="blue" loading={loading} subtitle="All time" />
          <KpiCard title="Conversion Rate" value={`${kpis?.conversion_rate || 0}%`} icon={Target} color="green" loading={loading} subtitle="Leads → Won" />
          <KpiCard title="Pipeline Value" value={formatCurrency(kpis?.total_pipeline_value)} icon={DollarSign} color="purple" loading={loading} subtitle="Active deals" />
          <KpiCard title="Avg Deal Size" value={formatCurrency(kpis?.avg_deal_size)} icon={TrendingUp} color="amber" loading={loading} subtitle="Per qualified lead" />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Leads Over Time" subtitle="Monthly new leads created" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={leadsTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} strokeWidth={2} name="Leads" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Leads by Source" subtitle="Distribution of lead sources" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={bySource} dataKey="count" nameKey="category" cx="50%" cy="50%" outerRadius={100} label={({ category, count }) => `${category} (${count})`}>
                  {bySource.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Pipeline Funnel" subtitle="Leads and value by stage" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byStage} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="category" type="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v, name) => name === 'Value' ? formatCurrency(v) : v} />
                <Legend />
                <Bar dataKey="count" fill="#3B82F6" name="Count" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Leads by Owner" subtitle="Performance by sales rep" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={byOwner}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => name === 'Value' ? formatCurrency(v) : v} />
                <Legend />
                <Bar dataKey="count" fill="#3B82F6" name="Leads" radius={[4, 4, 0, 0]} />
                <Bar dataKey="value" fill="#10B981" name="Value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Leads by Region */}
        <ChartCard title="Leads by Region" subtitle="Geographic distribution" loading={loading}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={byRegion}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="category" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v, name) => name === 'Value' ? formatCurrency(v) : v} />
              <Legend />
              <Bar dataKey="count" fill="#8B5CF6" name="Leads" radius={[4, 4, 0, 0]} />
              <Bar dataKey="value" fill="#F59E0B" name="Value" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Stale Leads Table */}
        <DataTable
          title={`⚠️ Stale Leads (${stale.length})`}
          columns={staleColumns}
          data={stale}
          collapsible
          defaultCollapsed={false}
          loading={loading}
          emptyMessage="No stale leads found"
        />
      </div>
    </div>
  );
}
