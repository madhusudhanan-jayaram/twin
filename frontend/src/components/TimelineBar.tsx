import { MapPin, Flag } from 'lucide-react';
import type { SensorData } from '../hooks/useWebSocket';

interface TimelineBarProps {
  sensorData: SensorData | null;
  totalWaypoints: number;
}

export default function TimelineBar({ sensorData, totalWaypoints }: TimelineBarProps) {
  const progress = sensorData
    ? Math.min(100, (sensorData.waypoint_index / totalWaypoints) * 100)
    : 0;

  const simHours = sensorData ? sensorData.sim_minutes / 60 : 0;

  return (
    <div className="bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-medium text-slate-300">Dallas, TX</span>
        </div>
        <div className="text-xs text-slate-400">
          Sim Time: {Math.floor(simHours)}h {String(Math.floor(sensorData?.sim_minutes ?? 0) % 60).padStart(2, '0')}m
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-300">Chicago, IL</span>
          <Flag className="w-4 h-4 text-green-400" />
        </div>
      </div>

      <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${progress}%`,
            background: sensorData?.status === 'rerouting'
              ? 'linear-gradient(90deg, #3b82f6, #f97316)'
              : sensorData?.status === 'delayed'
              ? 'linear-gradient(90deg, #3b82f6, #eab308)'
              : 'linear-gradient(90deg, #3b82f6, #22c55e)',
          }}
        />
        {/* Truck indicator */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg shadow-blue-500/30 transition-all duration-500"
          style={{ left: `calc(${progress}% - 6px)` }}
        />
      </div>

      <div className="flex justify-between mt-1.5 text-[10px] text-slate-500">
        <span>{progress.toFixed(0)}% complete</span>
        <span>{sensorData?.phase_description ?? 'Waiting to start'}</span>
      </div>
    </div>
  );
}
