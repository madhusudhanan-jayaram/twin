import { useEffect, useRef, useState, useCallback } from 'react';

export interface SensorData {
  shipment_id: number;
  tick: number;
  sim_minutes: number;
  lat: number;
  lng: number;
  temperature: number;
  humidity: number;
  speed: number;
  status: string;
  spoilage_hours: number | null;
  waypoint_index: number;
  phase: string;
  phase_description: string;
}

export interface AlertData {
  type: string;
  severity: string;
  message: string;
  timestamp: string;
}

export interface ApprovalRequest {
  alert_id: number;
  proposal: string;
  warehouse: {
    id: number;
    name: string;
    city: string;
    state: string;
    lat: number;
    lng: number;
    distance_miles: number;
  };
  temperature: number;
  spoilage_hours: number | null;
  risk_level: string;
}

export interface RouteUpdate {
  type: string;
  warehouse: {
    name: string;
    lat: number;
    lng: number;
    city: string;
    state: string;
  };
}

export interface ReportReady {
  report_id: number;
  disposition: string;
  summary: string;
  pct_in_range: number;
}

export interface WebSocketState {
  connected: boolean;
  sensorData: SensorData | null;
  sensorHistory: SensorData[];
  alerts: AlertData[];
  approvalRequest: ApprovalRequest | null;
  routeUpdate: RouteUpdate | null;
  reportReady: ReportReady | null;
}

export function useWebSocket() {
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    sensorData: null,
    sensorHistory: [],
    alerts: [],
    approvalRequest: null,
    routeUpdate: null,
    reportReady: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number>();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setState(prev => ({ ...prev, connected: true }));
    };

    ws.onclose = () => {
      setState(prev => ({ ...prev, connected: false }));
      reconnectTimerRef.current = window.setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { type, data } = msg;

        setState(prev => {
          switch (type) {
            case 'sensor_update':
              return {
                ...prev,
                sensorData: data,
                sensorHistory: [...prev.sensorHistory.slice(-120), data],
              };
            case 'alert':
              return {
                ...prev,
                alerts: [data, ...prev.alerts].slice(0, 50),
              };
            case 'approval_request':
              return { ...prev, approvalRequest: data };
            case 'approval_decision':
              return { ...prev, approvalRequest: null };
            case 'route_update':
              return { ...prev, routeUpdate: data };
            case 'report_ready':
              return { ...prev, reportReady: data };
            default:
              return prev;
          }
        });
      } catch {
        // ignore parse errors
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, [connect]);

  const clearApproval = useCallback(() => {
    setState(prev => ({ ...prev, approvalRequest: null }));
  }, []);

  const clearReport = useCallback(() => {
    setState(prev => ({ ...prev, reportReady: null }));
  }, []);

  return { ...state, clearApproval, clearReport };
}
