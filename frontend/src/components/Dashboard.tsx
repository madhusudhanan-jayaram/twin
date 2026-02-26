import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import LiveMap from './LiveMap';
import SensorCharts from './SensorCharts';
import DigitalTwinPanel from './DigitalTwinPanel';
import AlertPanel from './AlertPanel';
import ApprovalDialog from './ApprovalDialog';
import FDAReportViewer from './FDAReportViewer';
import TimelineBar from './TimelineBar';
import { Activity, Play, Square, RotateCcw, Wifi, WifiOff } from 'lucide-react';

interface Warehouse {
  id: number;
  name: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
}

export default function Dashboard() {
  const ws = useWebSocket();
  const [route, setRoute] = useState<Array<{ lat: number; lng: number }>>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [simRunning, setSimRunning] = useState(false);
  const [showReport, setShowReport] = useState(false);

  // Fetch route and warehouses on mount
  useEffect(() => {
    fetch('/api/route')
      .then(r => r.json())
      .then(data => setRoute(data.waypoints))
      .catch(() => {});

    fetch('/api/warehouses')
      .then(r => r.json())
      .then(data => setWarehouses(data))
      .catch(() => {});
  }, []);

  // Show report viewer when report is ready
  useEffect(() => {
    if (ws.reportReady) setShowReport(true);
  }, [ws.reportReady]);

  const startSimulation = useCallback(async () => {
    await fetch('/api/simulation/start', { method: 'POST' });
    setSimRunning(true);
  }, []);

  const stopSimulation = useCallback(async () => {
    await fetch('/api/simulation/stop', { method: 'POST' });
    setSimRunning(false);
  }, []);

  const resetSimulation = useCallback(async () => {
    await fetch('/api/simulation/reset', { method: 'POST' });
    setSimRunning(false);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-blue-400" />
          <h1 className="text-lg font-bold text-slate-200">Cold Chain Integrity Monitor</h1>
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Agentic AI Demo</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className={`flex items-center gap-1.5 text-xs ${ws.connected ? 'text-green-400' : 'text-red-400'}`}>
            {ws.connected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
            {ws.connected ? 'Connected' : 'Disconnected'}
          </div>

          {/* Simulation controls */}
          <div className="flex items-center gap-1.5 border-l border-slate-700 pl-3">
            {!simRunning ? (
              <button
                onClick={startSimulation}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-500 transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                Start Demo
              </button>
            ) : (
              <button
                onClick={stopSimulation}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-500 transition-colors"
              >
                <Square className="w-3.5 h-3.5" />
                Stop
              </button>
            )}
            <button
              onClick={resetSimulation}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 text-slate-300 text-xs font-medium rounded-lg hover:bg-slate-600 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          </div>
        </div>
      </header>

      {/* Timeline bar */}
      <div className="px-6 py-2 bg-slate-900/50">
        <TimelineBar sensorData={ws.sensorData} totalWaypoints={200} />
      </div>

      {/* Main content: 60% map / 40% panels */}
      <div className="flex-1 flex min-h-0 p-4 gap-4">
        {/* Left: Map */}
        <div className="w-3/5 h-full">
          <LiveMap
            sensorData={ws.sensorData}
            routeUpdate={ws.routeUpdate}
            route={route}
            warehouses={warehouses}
          />
        </div>

        {/* Right: Panels */}
        <div className="w-2/5 h-full overflow-y-auto space-y-4 pr-1">
          <DigitalTwinPanel sensorData={ws.sensorData} />
          <SensorCharts sensorHistory={ws.sensorHistory} />
          <AlertPanel alerts={ws.alerts} />
        </div>
      </div>

      {/* Modals */}
      <ApprovalDialog
        request={ws.approvalRequest}
        onClose={ws.clearApproval}
      />

      {/* FDA Report slide-in */}
      {showReport && (
        <FDAReportViewer
          reportReady={ws.reportReady}
          onClose={() => {
            setShowReport(false);
            ws.clearReport();
          }}
        />
      )}
    </div>
  );
}
