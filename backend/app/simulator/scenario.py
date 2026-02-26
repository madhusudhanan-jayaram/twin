"""Scripted crisis events for the demo scenario."""

from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    NORMAL = "normal"
    TRAFFIC_DELAY = "traffic_delay"
    FRIDGE_PARTIAL_FAIL = "fridge_partial_fail"
    FRIDGE_FULL_FAIL = "fridge_full_fail"
    REROUTING = "rerouting"
    AT_WAREHOUSE = "at_warehouse"
    RESUME_NORMAL = "resume_normal"


@dataclass
class ScenarioPhase:
    """Defines behavior during a range of simulation ticks."""
    start_tick: int
    event_type: EventType
    speed_mph: float = 65.0
    temp_drift_per_tick: float = 0.0  # °C change per tick
    humidity_drift_per_tick: float = 0.0
    description: str = ""


# Each tick = 2 real seconds = 5 sim minutes
# Total ~90 ticks for a 3-minute demo (180 real seconds / 2)

SCENARIO_PHASES: list[ScenarioPhase] = [
    # Phase 1: Normal transit (ticks 0-44, ~90 sec real, ~0-3.7 sim hours)
    ScenarioPhase(
        start_tick=0,
        event_type=EventType.NORMAL,
        speed_mph=65.0,
        temp_drift_per_tick=0.0,
        humidity_drift_per_tick=0.0,
        description="Normal transit from Dallas. Refrigeration nominal.",
    ),
    # Phase 2: Traffic delay near Ardmore (ticks 45-52, ~14 sec real)
    ScenarioPhase(
        start_tick=45,
        event_type=EventType.TRAFFIC_DELAY,
        speed_mph=15.0,
        temp_drift_per_tick=0.05,
        humidity_drift_per_tick=0.3,
        description="Traffic congestion near Ardmore, OK. Speed reduced.",
    ),
    # Phase 3: Refrigeration partial failure (ticks 53-59, ~14 sec real)
    ScenarioPhase(
        start_tick=53,
        event_type=EventType.FRIDGE_PARTIAL_FAIL,
        speed_mph=45.0,
        temp_drift_per_tick=0.15,
        humidity_drift_per_tick=0.5,
        description="Refrigeration unit partial failure detected. Temperature rising.",
    ),
    # Phase 4: Critical - temp hits threshold (ticks 60+, agent should trigger)
    ScenarioPhase(
        start_tick=60,
        event_type=EventType.FRIDGE_FULL_FAIL,
        speed_mph=45.0,
        temp_drift_per_tick=0.25,
        humidity_drift_per_tick=0.8,
        description="Refrigeration failure confirmed. Temperature rising rapidly.",
    ),
]


def get_phase_for_tick(tick: int) -> ScenarioPhase:
    """Return the active scenario phase for the given tick."""
    active = SCENARIO_PHASES[0]
    for phase in SCENARIO_PHASES:
        if tick >= phase.start_tick:
            active = phase
    return active


# Reroute destination waypoint index (OKC area, roughly waypoint ~60)
REROUTE_WAYPOINT_INDEX = 60
