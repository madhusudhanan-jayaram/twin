"""Sensor data generator with scripted scenario events."""

import asyncio
import logging
import random
from datetime import datetime

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Shipment, SensorReading, ShipmentStatus
from app.simulator.route import get_waypoint, TOTAL_WAYPOINTS, ROUTE_WAYPOINTS
from app.simulator.scenario import get_phase_for_tick, EventType
from app.simulator.thermal_model import predict_spoilage_hours, compute_cumulative_exposure

logger = logging.getLogger(__name__)


class SensorSimulator:
    def __init__(self):
        self.tick = 0
        self.running = False
        self.temperature = 4.0
        self.humidity = 45.0
        self.waypoint_index = 0
        self.base_temp = 4.0
        self.rerouting = False
        self.reroute_target_lat: float | None = None
        self.reroute_target_lng: float | None = None
        self.at_warehouse = False
        self.warehouse_arrival_tick: int | None = None
        self._callbacks: list = []
        self._agent_triggered = False
        self._all_temps: list[float] = []

    def on_update(self, callback):
        self._callbacks.append(callback)

    async def _notify(self, event_type: str, data: dict):
        for cb in self._callbacks:
            try:
                await cb(event_type, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def reset(self):
        self.tick = 0
        self.temperature = 4.0
        self.humidity = 45.0
        self.waypoint_index = 0
        self.rerouting = False
        self.reroute_target_lat = None
        self.reroute_target_lng = None
        self.at_warehouse = False
        self.warehouse_arrival_tick = None
        self._agent_triggered = False
        self._all_temps = []

    def start_reroute(self, target_lat: float, target_lng: float):
        """Called when agent approves reroute to warehouse."""
        self.rerouting = True
        self.reroute_target_lat = target_lat
        self.reroute_target_lng = target_lng

    async def run(self, session_factory):
        self.running = True
        self.reset()
        logger.info("Simulation started")

        async with session_factory() as session:
            # Create or reset shipment
            result = await session.execute(select(Shipment))
            shipment = result.scalars().first()
            if not shipment:
                shipment = Shipment()
                session.add(shipment)
            else:
                shipment.status = ShipmentStatus.in_transit
                shipment.current_lat = 32.7767
                shipment.current_lng = -96.7970
                shipment.current_temperature = 4.0
                shipment.current_humidity = 45.0
                shipment.waypoint_index = 0
                shipment.predicted_spoilage_hours = None
            await session.commit()
            await session.refresh(shipment)
            shipment_id = shipment.id

        while self.running:
            await asyncio.sleep(settings.simulation_tick_seconds)
            self.tick += 1

            phase = get_phase_for_tick(self.tick)

            # Handle rerouting / at_warehouse overrides
            if self.at_warehouse:
                # Temperature stabilizing at warehouse
                self.temperature = max(4.0, self.temperature - 0.3)
                self.humidity = max(45.0, self.humidity - 0.5)
                speed = 0.0

                # After ~15 ticks at warehouse, generate report
                if self.warehouse_arrival_tick and self.tick - self.warehouse_arrival_tick > 15:
                    await self._notify("report_ready", {"shipment_id": shipment_id})
                    self.running = False
                    break
            elif self.rerouting:
                # Moving toward warehouse
                if self.reroute_target_lat and self.reroute_target_lng:
                    wp = get_waypoint(self.waypoint_index)
                    dlat = self.reroute_target_lat - wp.lat
                    dlng = self.reroute_target_lng - wp.lng
                    dist = (dlat**2 + dlng**2) ** 0.5
                    if dist < 0.05:  # Close enough
                        self.at_warehouse = True
                        self.warehouse_arrival_tick = self.tick
                        self.temperature = max(self.temperature, self.temperature)
                    else:
                        step = min(0.15, dist)
                        ratio = step / dist
                        new_lat = wp.lat + dlat * ratio
                        new_lng = wp.lng + dlng * ratio
                        self.waypoint_index = min(self.waypoint_index + 1, TOTAL_WAYPOINTS - 1)
                        # Override waypoint position
                        ROUTE_WAYPOINTS[self.waypoint_index] = type(wp)(lat=new_lat, lng=new_lng)
                speed = 35.0
                self.temperature += 0.05  # Still rising but slower
                self.humidity += 0.2
            else:
                # Normal scenario-driven updates
                noise_t = random.gauss(0, 0.05)
                noise_h = random.gauss(0, 0.3)
                self.temperature += phase.temp_drift_per_tick + noise_t
                self.humidity += phase.humidity_drift_per_tick + noise_h
                speed = phase.speed_mph + random.gauss(0, 2)

                # Advance along route
                steps = max(1, int(speed / 65.0 * 2))
                self.waypoint_index = min(self.waypoint_index + steps, TOTAL_WAYPOINTS - 1)

            # Clamp values
            self.temperature = round(max(self.base_temp - 1, min(15.0, self.temperature)), 2)
            self.humidity = round(max(30.0, min(95.0, self.humidity)), 1)

            wp = get_waypoint(self.waypoint_index)
            sim_minutes = self.tick * settings.simulation_minutes_per_tick

            self._all_temps.append(self.temperature)

            # Compute spoilage prediction
            interval_hours = settings.simulation_minutes_per_tick / 60.0
            cumulative_dh = compute_cumulative_exposure(self._all_temps, interval_hours)

            # Estimate rise rate from recent readings
            if len(self._all_temps) >= 5:
                recent = self._all_temps[-5:]
                rise_rate = (recent[-1] - recent[0]) / (4 * interval_hours)
            else:
                rise_rate = 0.0

            spoilage_hours = predict_spoilage_hours(self.temperature, rise_rate, cumulative_dh)

            # Determine status
            if self.at_warehouse:
                status = ShipmentStatus.at_warehouse
            elif self.rerouting:
                status = ShipmentStatus.rerouting
            elif phase.event_type == EventType.TRAFFIC_DELAY:
                status = ShipmentStatus.delayed
            elif self.waypoint_index >= TOTAL_WAYPOINTS - 1:
                status = ShipmentStatus.delivered
            else:
                status = ShipmentStatus.in_transit

            # Save to DB
            async with session_factory() as session:
                reading = SensorReading(
                    shipment_id=shipment_id,
                    sim_minutes=sim_minutes,
                    lat=wp.lat,
                    lng=wp.lng,
                    temperature_celsius=self.temperature,
                    humidity_percent=self.humidity,
                    speed_mph=speed,
                )
                session.add(reading)

                result = await session.execute(select(Shipment).where(Shipment.id == shipment_id))
                shipment = result.scalars().first()
                if shipment:
                    shipment.current_lat = wp.lat
                    shipment.current_lng = wp.lng
                    shipment.current_temperature = self.temperature
                    shipment.current_humidity = self.humidity
                    shipment.waypoint_index = self.waypoint_index
                    shipment.predicted_spoilage_hours = spoilage_hours
                    shipment.status = status

                await session.commit()

            # Broadcast update
            sensor_data = {
                "shipment_id": shipment_id,
                "tick": self.tick,
                "sim_minutes": sim_minutes,
                "lat": wp.lat,
                "lng": wp.lng,
                "temperature": self.temperature,
                "humidity": self.humidity,
                "speed": round(speed, 1),
                "status": status.value,
                "spoilage_hours": round(spoilage_hours, 1) if spoilage_hours is not None else None,
                "waypoint_index": self.waypoint_index,
                "phase": phase.event_type.value,
                "phase_description": phase.description,
            }
            await self._notify("sensor_update", sensor_data)

            # Check if agent should trigger
            if (
                not self._agent_triggered
                and self.temperature >= settings.temperature_threshold_celsius
                and not self.rerouting
                and not self.at_warehouse
            ):
                self._agent_triggered = True
                await self._notify("trigger_agent", {
                    "shipment_id": shipment_id,
                    "temperature": self.temperature,
                    "humidity": self.humidity,
                    "lat": wp.lat,
                    "lng": wp.lng,
                    "spoilage_hours": spoilage_hours,
                    "tick": self.tick,
                })

            if status == ShipmentStatus.delivered:
                self.running = False
                break

        logger.info("Simulation ended")


# Global simulator instance
simulator = SensorSimulator()
