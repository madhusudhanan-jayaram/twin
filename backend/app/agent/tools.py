"""Agent tools for cold chain management."""

import math
from sqlmodel import select
from app.db.database import async_session
from app.models import Warehouse, SensorReading


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in miles between two lat/lng points."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(a**0.5, (1 - a) ** 0.5)
    return R * c


async def find_nearby_warehouses(lat: float, lng: float, radius_miles: float = 50.0) -> list[dict]:
    """Find pharma-certified warehouses within radius of current position."""
    async with async_session() as session:
        result = await session.execute(select(Warehouse))
        warehouses = result.scalars().all()

    nearby = []
    for wh in warehouses:
        dist = haversine_miles(lat, lng, wh.lat, wh.lng)
        if dist <= radius_miles:
            nearby.append({
                "id": wh.id,
                "name": wh.name,
                "city": wh.city,
                "state": wh.state,
                "lat": wh.lat,
                "lng": wh.lng,
                "distance_miles": round(dist, 1),
                "available_capacity": wh.available_capacity,
                "temp_range": f"{wh.temp_min}-{wh.temp_max}°C",
                "is_pharma_certified": wh.is_pharma_certified,
            })

    nearby.sort(key=lambda x: x["distance_miles"])
    return nearby


async def get_sensor_history(shipment_id: int, last_n: int = 20) -> list[dict]:
    """Get recent sensor readings for analysis."""
    async with async_session() as session:
        result = await session.execute(
            select(SensorReading)
            .where(SensorReading.shipment_id == shipment_id)
            .order_by(SensorReading.id.desc())
            .limit(last_n)
        )
        readings = result.scalars().all()

    return [
        {
            "timestamp": r.timestamp,
            "sim_minutes": r.sim_minutes,
            "temperature": r.temperature_celsius,
            "humidity": r.humidity_percent,
            "speed": r.speed_mph,
            "lat": r.lat,
            "lng": r.lng,
        }
        for r in reversed(readings)
    ]
