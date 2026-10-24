import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
});

// Data endpoints
export const loadData = () => API.get('/data/load');
export const getDataStatus = () => API.get('/data/status');

// Sales endpoints
export const getSalesKpis = (params) => API.get('/sales/kpis', { params });
export const getLeadsOverTime = (params) => API.get('/sales/leads-over-time', { params });
export const getLeadsBySource = (params) => API.get('/sales/leads-by-source', { params });
export const getLeadsByStage = (params) => API.get('/sales/leads-by-stage', { params });
export const getLeadsByOwner = (params) => API.get('/sales/leads-by-owner', { params });
export const getLeadsByRegion = (params) => API.get('/sales/leads-by-region', { params });
export const getStageConversion = (params) => API.get('/sales/stage-conversion', { params });
export const getStaleLeads = (params) => API.get('/sales/stale-leads', { params });

// Operations endpoints
export const getOpsKpis = (params) => API.get('/operations/kpis', { params });
export const getProjectsByStatus = (params) => API.get('/operations/projects-by-status', { params });
export const getProjectsOverTime = (params) => API.get('/operations/projects-over-time', { params });
export const getWorkloadByTeam = (params) => API.get('/operations/workload-by-team', { params });
export const getWorkloadByService = (params) => API.get('/operations/workload-by-service', { params });
export const getSlaOverview = (params) => API.get('/operations/sla-overview', { params });
export const getTargetsVsActuals = (params) => API.get('/operations/targets-vs-actuals', { params });
export const getOverdueProjects = (params) => API.get('/operations/overdue-projects', { params });

// Combined view
export const getSalesToOps = (params) => API.get('/combined/sales-to-ops', { params });

// Data quality
export const getDataQualitySummary = () => API.get('/data-quality/summary');
export const getDataQualityUnmatched = () => API.get('/data-quality/unmatched');

// AI Insights
export const getInsights = () => API.get('/insights');
export const getInsight = (type) => API.get(`/insights/${type}`);

// Filter options
export const getFilterOptions = () => API.get('/filters/options');

export default API;
