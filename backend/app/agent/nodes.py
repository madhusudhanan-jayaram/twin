"""LangGraph node functions for the cold chain agent."""

import logging
from datetime import datetime

from app.agent.state import ColdChainAgentState
from app.agent.tools import find_nearby_warehouses, get_sensor_history
from app.config import settings

logger = logging.getLogger(__name__)


async def detect_anomaly(state: ColdChainAgentState) -> dict:
    """Check if current sensor data indicates an anomaly."""
    temp = state["current_temperature"]
    threshold = settings.temperature_threshold_celsius

    if temp >= threshold:
        return {
            "anomaly_detected": True,
            "messages": [{"role": "assistant", "content": f"ANOMALY DETECTED: Temperature {temp}°C exceeds threshold {threshold}°C"}],
        }
    return {
        "anomaly_detected": False,
        "messages": [{"role": "assistant", "content": f"Temperature {temp}°C is within normal range."}],
    }


async def assess_risk(state: ColdChainAgentState) -> dict:
    """Assess the risk level based on temperature and spoilage prediction."""
    temp = state["current_temperature"]
    spoilage = state.get("spoilage_hours")

    if temp >= settings.critical_temperature_celsius or (spoilage is not None and spoilage < 2):
        risk_level = "critical"
        assessment = (
            f"CRITICAL: Temperature at {temp}°C. "
            f"Estimated spoilage in {spoilage:.1f} hours. "
            f"Skyrizi (risankizumab) requires 2-8°C storage per FDA guidelines. "
            f"Immediate intervention required to prevent product loss worth ~$250,000."
        )
    elif temp >= settings.temperature_threshold_celsius:
        risk_level = "high"
        spoilage_str = f"{spoilage:.1f} hours" if spoilage else "calculating"
        assessment = (
            f"HIGH RISK: Temperature at {temp}°C, exceeding {settings.temperature_threshold_celsius}°C threshold. "
            f"Predicted spoilage in {spoilage_str}. "
            f"Refrigeration failure detected. Recommend immediate reroute to certified cold storage."
        )
    else:
        risk_level = "medium"
        assessment = f"ELEVATED: Temperature {temp}°C trending upward. Monitoring closely."

    return {
        "risk_level": risk_level,
        "risk_assessment": assessment,
        "messages": [{"role": "assistant", "content": assessment}],
    }


async def find_warehouses(state: ColdChainAgentState) -> dict:
    """Find nearby warehouses that can accept the shipment."""
    lat = state["current_lat"]
    lng = state["current_lng"]

    warehouses = await find_nearby_warehouses(lat, lng, radius_miles=100.0)

    if not warehouses:
        return {
            "nearby_warehouses": [],
            "recommended_warehouse": None,
            "messages": [{"role": "assistant", "content": "No nearby warehouses found within 100 miles."}],
        }

    recommended = warehouses[0]  # Closest one

    msg = (
        f"Found {len(warehouses)} nearby warehouse(s). "
        f"Recommending: {recommended['name']} in {recommended['city']}, {recommended['state']} "
        f"({recommended['distance_miles']} miles away, capacity: {recommended['available_capacity']} units)."
    )

    return {
        "nearby_warehouses": warehouses,
        "recommended_warehouse": recommended,
        "messages": [{"role": "assistant", "content": msg}],
    }


async def propose_reroute(state: ColdChainAgentState) -> dict:
    """Create a reroute proposal for human approval."""
    wh = state.get("recommended_warehouse")
    if not wh:
        return {
            "reroute_proposal": "No warehouse available for reroute.",
            "messages": [{"role": "assistant", "content": "Cannot propose reroute - no suitable warehouse found."}],
        }

    spoilage = state.get("spoilage_hours")
    spoilage_str = f"{spoilage:.1f} hours" if spoilage else "unknown"

    proposal = (
        f"REROUTE RECOMMENDATION\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Drug: Skyrizi (risankizumab) - Batch SKZ-2024-0847\n"
        f"Current Temp: {state['current_temperature']}°C (threshold: {settings.temperature_threshold_celsius}°C)\n"
        f"Spoilage ETA: {spoilage_str}\n"
        f"Risk Level: {state.get('risk_level', 'high').upper()}\n\n"
        f"Destination: {wh['name']}\n"
        f"Location: {wh['city']}, {wh['state']}\n"
        f"Distance: {wh['distance_miles']} miles\n"
        f"ETA: ~{int(wh['distance_miles'] / 35 * 60)} minutes\n"
        f"Capacity: {wh['available_capacity']} units available\n"
        f"Temp Range: {wh['temp_range']}\n"
        f"Pharma Certified: {'Yes' if wh['is_pharma_certified'] else 'No'}\n\n"
        f"ACTION REQUIRED: Approve or reject this reroute."
    )

    return {
        "reroute_proposal": proposal,
        "messages": [{"role": "assistant", "content": proposal}],
    }


async def execute_reroute(state: ColdChainAgentState) -> dict:
    """Execute the approved reroute."""
    wh = state.get("recommended_warehouse")
    if not wh:
        return {"messages": [{"role": "assistant", "content": "No warehouse to reroute to."}]}

    # The actual reroute is handled by the simulator via the callback
    msg = (
        f"Reroute APPROVED and executing. "
        f"Truck redirecting to {wh['name']} ({wh['distance_miles']} miles). "
        f"Estimated arrival: ~{int(wh['distance_miles'] / 35 * 60)} minutes."
    )

    return {
        "messages": [{"role": "assistant", "content": msg}],
    }


async def generate_report(state: ColdChainAgentState) -> dict:
    """Generate FDA compliance report."""
    return {
        "report_generated": True,
        "messages": [{"role": "assistant", "content": "FDA compliance report generation initiated."}],
    }


async def log_rejection(state: ColdChainAgentState) -> dict:
    """Log that the reroute was rejected."""
    return {
        "messages": [{"role": "assistant", "content": "Reroute REJECTED by operator. Continuing on original route. Risk acknowledged."}],
    }
