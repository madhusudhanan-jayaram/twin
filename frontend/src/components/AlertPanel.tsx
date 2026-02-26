import { AlertTriangle, Info, AlertCircle, Bell } from 'lucide-react';
import type { AlertData } from '../hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

interface AlertPanelProps {
  alerts: AlertData[];
}

function getSeverityIcon(severity: string) {
  switch (severity) {
    case 'critical':
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    case 'warning':
      return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
    default:
      return <Info className="w-4 h-4 text-blue-400" />;
  }
}

function getSeverityBadge(severity: string) {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'warning':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    default:
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
  }
}

export default function AlertPanel({ alerts }: AlertPanelProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
        <Bell className="w-4 h-4 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-300">Alerts</h3>
        {alerts.length > 0 && (
          <span className="ml-auto bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full text-xs font-medium">
            {alerts.length}
          </span>
        )}
      </div>

      <div className="max-h-64 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="px-4 py-6 text-center text-slate-500 text-sm">
            No alerts yet
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {alerts.map((alert, i) => (
              <div key={i} className="px-4 py-3 hover:bg-slate-700/20 transition-colors">
                <div className="flex items-start gap-2">
                  {getSeverityIcon(alert.severity)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {alert.timestamp ? formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true }) : 'just now'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
