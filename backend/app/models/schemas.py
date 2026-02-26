from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column


class LatLng(BaseModel):
    lat: float
    lng: float


# ---------- enums ----------

class ShipmentStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    delayed = "delayed"
    rerouting = "rerouting"
    delivered = "delivered"
    at_warehouse = "at_warehouse"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class HumanDecision(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Disposition(str, enum.Enum):
    PASS = "PASS"
    CONDITIONAL = "CONDITIONAL"
    FAIL = "FAIL"


# ---------- DB models ----------

class Shipment(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    drug_name: str = "Skyrizi (risankizumab)"
    batch_number: str = "SKZ-2024-0847"
    origin_city: str = "Dallas, TX"
    origin_lat: float = 32.7767
    origin_lng: float = -96.7970
    destination_city: str = "Chicago, IL"
    destination_lat: float = 41.8781
    destination_lng: float = -87.6298
    status: ShipmentStatus = ShipmentStatus.in_transit
    current_lat: float = 32.7767
    current_lng: float = -96.7970
    current_temperature: float = 4.0
    current_humidity: float = 45.0
    predicted_spoilage_hours: Optional[float] = None
    waypoint_index: int = 0
    created_at: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())


class SensorReading(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    shipment_id: int
    timestamp: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())
    sim_minutes: float = 0.0
    lat: float
    lng: float
    temperature_celsius: float
    humidity_percent: float
    speed_mph: float = 65.0


class Warehouse(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str
    city: str
    state: str
    lat: float
    lng: float
    available_capacity: int
    temp_min: float = 2.0
    temp_max: float = 8.0
    is_pharma_certified: bool = True


class Alert(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    shipment_id: int
    timestamp: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())
    alert_type: str  # temperature_warning, temperature_critical, reroute_proposal
    severity: AlertSeverity = AlertSeverity.info
    message: str = ""
    ai_recommendation: Optional[str] = None
    proposed_warehouse_id: Optional[int] = None
    proposed_warehouse_name: Optional[str] = None
    human_decision: HumanDecision = HumanDecision.pending
    thread_id: Optional[str] = None


class ComplianceReport(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    shipment_id: int
    created_at: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())
    summary: str = ""
    temperature_log_summary: str = ""
    excursion_events: str = ""
    total_time_in_range_percent: float = 100.0
    max_temperature_recorded: float = 0.0
    min_temperature_recorded: float = 0.0
    disposition: Disposition = Disposition.PASS
    full_report: str = ""
