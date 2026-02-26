import { Thermometer, Droplets, Clock, Gauge } from 'lucide-react';
import type { SensorData } from '../hooks/useWebSocket';

interface DigitalTwinPanelProps {
  sensorData: SensorData | null;
}

function getTempColor(temp: number): string {
  if (temp >= 8) return 'text-red-400';
  if (temp >= 6) return 'text-yellow-400';
  if (temp >= 2) return 'text-green-400';
  return 'text-blue-400';
}

function getTempBg(temp: number): string {
  if (temp >= 8) return 'bg-red-500/10 border-red-500/30';
  if (temp >= 6) return 'bg-yellow-500/10 border-yellow-500/30';
  return 'bg-green-500/10 border-green-500/30';
}

function getStatusBadge(status: string) {
  const colors: Record<string, string> = {
    in_transit: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    delayed: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    rerouting: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    at_warehouse: 'bg-green-500/20 text-green-400 border-green-500/30',
    delivered: 'bg-green-500/20 text-green-400 border-green-500/30',
  };
  return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

export default function DigitalTwinPanel({ sensorData }: DigitalTwinPanelProps) {
  const temp = sensorData?.temperature ?? 4.0;
  const humidity = sensorData?.humidity ?? 45.0;
  const speed = sensorData?.speed ?? 0;
  const spoilage = sensorData?.spoilage_hours;
  const status = sensorData?.status ?? 'pending';

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-300">Digital Twin</h3>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusBadge(status)}`}>
          {status.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Big temperature display */}
      <div className={`rounded-xl p-6 border mb-4 text-center ${getTempBg(temp)}`}>
        <Thermometer className={`w-8 h-8 mx-auto mb-2 ${getTempColor(temp)}`} />
        <div className={`text-5xl font-bold tabular-nums ${getTempColor(temp)}`}>
          {temp.toFixed(1)}°
        </div>
        <div className="text-sm text-slate-400 mt-1">Celsius</div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Droplets className="w-3.5 h-3.5" />
            <span className="text-xs">Humidity</span>
          </div>
          <div className="text-lg font-semibold text-purple-400">{humidity.toFixed(0)}%</div>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Gauge className="w-3.5 h-3.5" />
            <span className="text-xs">Speed</span>
          </div>
          <div className="text-lg font-semibold text-slate-200">{speed.toFixed(0)} mph</div>
        </div>

        <div className="col-span-2 bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Clock className="w-3.5 h-3.5" />
            <span className="text-xs">Spoilage Countdown</span>
          </div>
          {spoilage !== null && spoilage !== undefined ? (
            <div className={`text-2xl font-bold ${spoilage < 3 ? 'text-red-400' : spoilage < 6 ? 'text-yellow-400' : 'text-green-400'}`}>
              {spoilage.toFixed(1)}h
              <span className="text-sm font-normal text-slate-400 ml-2">until spoilage</span>
            </div>
          ) : (
            <div className="text-lg font-semibold text-green-400">
              No risk detected
            </div>
          )}
        </div>
      </div>

      {/* Drug info */}
      <div className="mt-4 pt-3 border-t border-slate-700/50">
        <div className="text-xs text-slate-500 space-y-1">
          <div><span className="text-slate-400">Drug:</span> Skyrizi (risankizumab)</div>
          <div><span className="text-slate-400">Batch:</span> SKZ-2024-0847</div>
          <div><span className="text-slate-400">Req. Temp:</span> 2-8°C</div>
        </div>
      </div>
    </div>
  );
}
