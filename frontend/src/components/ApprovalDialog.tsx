import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ShieldAlert, MapPin, Clock, Thermometer, X, CheckCircle, XCircle } from 'lucide-react';
import type { ApprovalRequest } from '../hooks/useWebSocket';

interface ApprovalDialogProps {
  request: ApprovalRequest | null;
  onClose: () => void;
}

export default function ApprovalDialog({ request, onClose }: ApprovalDialogProps) {
  const [submitting, setSubmitting] = useState(false);

  if (!request) return null;

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    setSubmitting(true);
    try {
      await fetch(`/api/alerts/${request.alert_id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      });
      onClose();
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={!!request} onOpenChange={() => onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg bg-slate-900 border border-slate-600 rounded-2xl shadow-2xl p-0 overflow-hidden">
          {/* Header */}
          <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-4">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-6 h-6 text-red-400" />
              <div>
                <Dialog.Title className="text-lg font-bold text-red-400">
                  Reroute Approval Required
                </Dialog.Title>
                <Dialog.Description className="text-sm text-slate-400">
                  AI agent recommends immediate action
                </Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <button className="ml-auto text-slate-500 hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 space-y-4">
            {/* Risk metrics */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-800 rounded-lg p-3 text-center border border-slate-700">
                <Thermometer className="w-5 h-5 text-red-400 mx-auto mb-1" />
                <div className="text-xl font-bold text-red-400">{request.temperature}°C</div>
                <div className="text-[10px] text-slate-500">Current Temp</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-3 text-center border border-slate-700">
                <Clock className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                <div className="text-xl font-bold text-yellow-400">
                  {request.spoilage_hours?.toFixed(1) ?? '?'}h
                </div>
                <div className="text-[10px] text-slate-500">Until Spoilage</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-3 text-center border border-slate-700">
                <MapPin className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                <div className="text-xl font-bold text-orange-400">
                  {request.warehouse.distance_miles} mi
                </div>
                <div className="text-[10px] text-slate-500">To Warehouse</div>
              </div>
            </div>

            {/* Warehouse details */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
              <div className="text-sm font-semibold text-slate-300 mb-2">Recommended Destination</div>
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-green-400 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-slate-200">{request.warehouse.name}</div>
                  <div className="text-xs text-slate-400">{request.warehouse.city}, {request.warehouse.state}</div>
                  <div className="text-xs text-green-400 mt-1">Pharma-certified cold storage</div>
                </div>
              </div>
            </div>

            {/* Risk level */}
            <div className={`rounded-lg p-3 text-center border ${
              request.risk_level === 'critical'
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
            }`}>
              <div className="text-xs font-medium">
                Risk Level: {request.risk_level.toUpperCase()} — Estimated shipment value: ~$250,000
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="px-6 py-4 bg-slate-800/50 border-t border-slate-700 flex gap-3">
            <button
              onClick={() => handleDecision('rejected')}
              disabled={submitting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              <XCircle className="w-5 h-5" />
              Reject
            </button>
            <button
              onClick={() => handleDecision('approved')}
              disabled={submitting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-green-600 text-white font-semibold hover:bg-green-500 transition-colors disabled:opacity-50 shadow-lg shadow-green-900/30"
            >
              <CheckCircle className="w-5 h-5" />
              Approve Reroute
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
