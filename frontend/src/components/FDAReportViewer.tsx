import { useState, useEffect } from 'react';
import { FileText, X, Download, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import type { ReportReady } from '../hooks/useWebSocket';

interface FDAReportViewerProps {
  reportReady: ReportReady | null;
  onClose: () => void;
}

function DispositionBadge({ disposition }: { disposition: string }) {
  switch (disposition) {
    case 'PASS':
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-500/20 text-green-400 border border-green-500/30 text-sm font-semibold">
          <CheckCircle className="w-4 h-4" /> PASS
        </span>
      );
    case 'CONDITIONAL':
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 text-sm font-semibold">
          <AlertTriangle className="w-4 h-4" /> CONDITIONAL PASS
        </span>
      );
    case 'FAIL':
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 text-sm font-semibold">
          <XCircle className="w-4 h-4" /> FAIL
        </span>
      );
    default:
      return null;
  }
}

export default function FDAReportViewer({ reportReady, onClose }: FDAReportViewerProps) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (reportReady?.report_id) {
      setLoading(true);
      fetch(`/api/reports/${reportReady.report_id}`)
        .then(r => r.json())
        .then(data => {
          setReport(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [reportReady?.report_id]);

  if (!reportReady) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-xl z-50 slide-in">
      <div className="h-full bg-slate-900 border-l border-slate-700 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-700 bg-slate-800/50">
          <FileText className="w-5 h-5 text-blue-400" />
          <div className="flex-1">
            <h2 className="text-lg font-bold text-slate-200">FDA Compliance Report</h2>
            <p className="text-xs text-slate-400">21 CFR Part 211 — Cold Chain Assessment</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-700 transition-colors text-slate-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Disposition summary */}
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <DispositionBadge disposition={reportReady.disposition} />
          <div className="text-right">
            <div className="text-2xl font-bold text-slate-200">{reportReady.pct_in_range}%</div>
            <div className="text-xs text-slate-500">Time in Range</div>
          </div>
        </div>

        {/* Report content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
            </div>
          ) : report ? (
            <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
              {report.full_report}
            </pre>
          ) : (
            <div className="text-center text-slate-500 py-8">Loading report...</div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-700 bg-slate-800/50">
          <button
            onClick={() => {
              if (report?.full_report) {
                const blob = new Blob([report.full_report], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `FDA_Report_SKZ-2024-0847.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-500 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download Report
          </button>
        </div>
      </div>
    </div>
  );
}
