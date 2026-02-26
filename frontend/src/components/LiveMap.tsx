import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { SensorData, RouteUpdate } from '../hooks/useWebSocket';

// Truck icon
const truckIcon = L.divIcon({
  className: '',
  html: `<div style="position:relative;">
    <div class="truck-marker-pulse" style="position:absolute;width:24px;height:24px;border-radius:50%;background:rgba(59,130,246,0.3);top:-4px;left:-4px;"></div>
    <div style="width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #1e40af;box-shadow:0 0 12px rgba(59,130,246,0.6);"></div>
  </div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const truckIconWarning = L.divIcon({
  className: '',
  html: `<div style="position:relative;">
    <div class="truck-marker-pulse" style="position:absolute;width:24px;height:24px;border-radius:50%;background:rgba(239,68,68,0.3);top:-4px;left:-4px;"></div>
    <div style="width:16px;height:16px;border-radius:50%;background:#ef4444;border:3px solid #991b1b;box-shadow:0 0 12px rgba(239,68,68,0.6);"></div>
  </div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const warehouseIcon = L.divIcon({
  className: '',
  html: `<div style="width:12px;height:12px;border-radius:2px;background:#22c55e;border:2px solid #166534;box-shadow:0 0 8px rgba(34,197,94,0.4);"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

const targetWarehouseIcon = L.divIcon({
  className: '',
  html: `<div style="position:relative;">
    <div class="truck-marker-pulse" style="position:absolute;width:20px;height:20px;border-radius:50%;background:rgba(249,115,22,0.3);top:-4px;left:-4px;"></div>
    <div style="width:14px;height:14px;border-radius:2px;background:#f97316;border:2px solid #c2410c;box-shadow:0 0 12px rgba(249,115,22,0.6);"></div>
  </div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

interface Warehouse {
  id: number;
  name: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
}

function MapUpdater({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.panTo(center, { animate: true, duration: 0.5 });
    }
  }, [center, map]);
  return null;
}

interface LiveMapProps {
  sensorData: SensorData | null;
  routeUpdate: RouteUpdate | null;
  route: Array<{ lat: number; lng: number }>;
  warehouses: Warehouse[];
}

export default function LiveMap({ sensorData, routeUpdate, route, warehouses }: LiveMapProps) {
  const [followTruck, setFollowTruck] = useState(true);

  const routePositions = useMemo(
    () => route.map(wp => [wp.lat, wp.lng] as [number, number]),
    [route]
  );

  const truckPos: [number, number] | null = sensorData
    ? [sensorData.lat, sensorData.lng]
    : null;

  const isWarning = sensorData && sensorData.temperature > 6.0;

  // Reroute line
  const rerouteLine = useMemo(() => {
    if (!routeUpdate?.warehouse || !truckPos) return null;
    return [truckPos, [routeUpdate.warehouse.lat, routeUpdate.warehouse.lng] as [number, number]];
  }, [routeUpdate, truckPos]);

  return (
    <div className="relative h-full w-full rounded-lg overflow-hidden border border-slate-700">
      <MapContainer
        center={[37.5, -95.0]}
        zoom={6}
        className="h-full w-full"
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />

        {followTruck && truckPos && <MapUpdater center={truckPos} />}

        {/* Main route */}
        {routePositions.length > 0 && (
          <Polyline
            positions={routePositions}
            pathOptions={{ color: '#3b82f6', weight: 3, opacity: 0.6, dashArray: '8 4' }}
          />
        )}

        {/* Reroute line */}
        {rerouteLine && (
          <Polyline
            positions={rerouteLine}
            pathOptions={{ color: '#ef4444', weight: 4, opacity: 0.8, dashArray: '10 6' }}
          />
        )}

        {/* Origin marker */}
        <Marker position={[32.7767, -96.7970]} icon={L.divIcon({
          className: '',
          html: `<div style="width:10px;height:10px;border-radius:50%;background:#3b82f6;border:2px solid white;"></div>`,
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        })}>
          <Popup><span className="text-slate-900 font-semibold">Dallas, TX (Origin)</span></Popup>
        </Marker>

        {/* Destination marker */}
        <Marker position={[41.8781, -87.6298]} icon={L.divIcon({
          className: '',
          html: `<div style="width:10px;height:10px;border-radius:50%;background:#22c55e;border:2px solid white;"></div>`,
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        })}>
          <Popup><span className="text-slate-900 font-semibold">Chicago, IL (Destination)</span></Popup>
        </Marker>

        {/* Warehouse markers */}
        {warehouses.map(wh => (
          <Marker
            key={wh.id}
            position={[wh.lat, wh.lng]}
            icon={routeUpdate?.warehouse?.name === wh.name ? targetWarehouseIcon : warehouseIcon}
          >
            <Popup>
              <div className="text-slate-900">
                <div className="font-semibold">{wh.name}</div>
                <div className="text-sm">{wh.city}, {wh.state}</div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Truck marker */}
        {truckPos && (
          <Marker position={truckPos} icon={isWarning ? truckIconWarning : truckIcon}>
            <Popup>
              <div className="text-slate-900">
                <div className="font-semibold">Skyrizi Shipment</div>
                <div className="text-sm">Temp: {sensorData?.temperature}°C</div>
                <div className="text-sm">Speed: {sensorData?.speed} mph</div>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map controls overlay */}
      <div className="absolute top-3 right-3 z-[1000] flex gap-2">
        <button
          onClick={() => setFollowTruck(!followTruck)}
          className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            followTruck
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700/80'
          }`}
        >
          {followTruck ? 'Following' : 'Follow Truck'}
        </button>
      </div>

      {/* Status overlay */}
      {sensorData && (
        <div className="absolute bottom-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur px-3 py-2 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400">Status</div>
          <div className={`text-sm font-semibold ${
            sensorData.status === 'rerouting' ? 'text-orange-400' :
            sensorData.status === 'delayed' ? 'text-yellow-400' :
            sensorData.status === 'at_warehouse' ? 'text-green-400' :
            'text-blue-400'
          }`}>
            {sensorData.status.replace('_', ' ').toUpperCase()}
          </div>
        </div>
      )}
    </div>
  );
}
