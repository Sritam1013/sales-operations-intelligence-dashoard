import { useState, useEffect } from 'react';
import { Lightbulb, AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { getInsights } from '../api';
import { getSeverityColor } from '../utils';

function InsightCard({ insight }) {
  const [expanded, setExpanded] = useState(false);
  const colors = getSeverityColor(insight.severity);

  const SeverityIcon = insight.severity === 'critical' ? AlertTriangle
    : insight.severity === 'warning' ? AlertCircle : Info;

  return (
    <div className={`bg-white rounded-xl shadow-sm border ${colors.border} overflow-hidden hover:shadow-md transition-shadow`}>
      <div className="p-5">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${colors.bg} shrink-0`}>
            <SeverityIcon size={20} className={colors.text} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h3 className="text-base font-semibold text-slate-800">{insight.title}</h3>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
                {insight.severity}
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-3">{insight.description}</p>

            {/* Metric */}
            {insight.metric_value != null && (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg mb-3">
                <span className="text-xs text-slate-500 uppercase">Key Metric:</span>
                <span className="text-sm font-bold text-slate-800">{insight.metric_value}</span>
              </div>
            )}

            {/* Recommendation */}
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
              <p className="text-xs text-blue-500 uppercase font-medium mb-1">💡 Recommendation</p>
              <p className="text-sm text-blue-800">{insight.recommendation}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Linked Data (expandable) */}
      {insight.linked_data && insight.linked_data.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full px-5 py-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 hover:bg-slate-50 transition-colors"
          >
            <span>View linked data ({insight.linked_data.length} items)</span>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {expanded && (
            <div className="px-5 pb-4 max-h-64 overflow-y-auto">
              <pre className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg overflow-x-auto">
                {JSON.stringify(insight.linked_data, null, 2)}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function InsightsPage() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await getInsights();
        setInsights(res.data);
      } catch (err) {
        console.error('Error fetching insights:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const criticalCount = insights.filter((i) => i.severity === 'critical').length;
  const warningCount = insights.filter((i) => i.severity === 'warning').length;

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 bg-slate-200 rounded w-48 animate-pulse" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 animate-pulse">
            <div className="h-5 bg-slate-200 rounded w-64 mb-3" />
            <div className="h-3 bg-slate-200 rounded w-full mb-2" />
            <div className="h-3 bg-slate-200 rounded w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">AI-Assisted Insights</h2>
          <p className="text-sm text-slate-500 mt-1">Rule-based analytical insights derived from your data</p>
        </div>
        <div className="flex items-center gap-3">
          {criticalCount > 0 && (
            <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
              {criticalCount} Critical
            </span>
          )}
          {warningCount > 0 && (
            <span className="px-2.5 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
              {warningCount} Warnings
            </span>
          )}
          <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
            {insights.length} Total
          </span>
        </div>
      </div>

      {/* Sort: critical first, then warning, then info */}
      <div className="space-y-4">
        {[...insights]
          .sort((a, b) => {
            const order = { critical: 0, warning: 1, info: 2 };
            return (order[a.severity] || 2) - (order[b.severity] || 2);
          })
          .map((insight, i) => (
            <InsightCard key={i} insight={insight} />
          ))}
      </div>

      {insights.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <Lightbulb size={48} className="mx-auto mb-4 text-slate-300" />
          <p>No insights available. Click "Refresh Data" to load data first.</p>
        </div>
      )}
    </div>
  );
}
