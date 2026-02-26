import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine,
  ResponsiveContainer, Tooltip, Area, ComposedChart,
} from 'recharts';
import type { SensorData } from '../hooks/useWebSocket';

interface SensorChartsProps {
  sensorHistory: SensorData[];
}

export default function SensorCharts({ sensorHistory }: SensorChartsProps) {
  const data = sensorHistory.map((d, i) => ({
    idx: i,
    time: `${Math.floor(d.sim_minutes / 60)}h${String(Math.floor(d.sim_minutes % 60)).padStart(2, '0')}m`,
    temperature: d.temperature,
    humidity: d.humidity,
  }));

  return (
    <div className="space-y-4">
      {/* Temperature Chart */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Temperature (°C)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={10}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 12]}
              stroke="#64748b"
              fontSize={10}
              tickCount={7}
            />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' }}
              labelStyle={{ color: '#94a3b8' }}
            />
            {/* Safe range area */}
            <Area
              type="monotone"
              dataKey={() => 8}
              stroke="none"
              fill="#22c55e"
              fillOpacity={0.05}
              baseLine={2}
            />
            {/* Threshold lines */}
            <ReferenceLine y={8} stroke="#ef4444" strokeDasharray="5 3" label={{ value: '8°C Max', fill: '#ef4444', fontSize: 10, position: 'right' }} />
            <ReferenceLine y={6} stroke="#eab308" strokeDasharray="5 3" label={{ value: '6°C Warn', fill: '#eab308', fontSize: 10, position: 'right' }} />
            <ReferenceLine y={2} stroke="#3b82f6" strokeDasharray="5 3" label={{ value: '2°C Min', fill: '#3b82f6', fontSize: 10, position: 'right' }} />
            {/* Temperature line */}
            <Line
              type="monotone"
              dataKey="temperature"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#3b82f6' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Humidity Chart */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Humidity (%)</h3>
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={10}
              interval="preserveStartEnd"
            />
            <YAxis domain={[30, 80]} stroke="#64748b" fontSize={10} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: '12px' }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Line
              type="monotone"
              dataKey="humidity"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
