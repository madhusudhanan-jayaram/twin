"""LangGraph agent state definition."""

from __future__ import annotations

from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages


class ColdChainAgentState(TypedDict):
    """State for the cold chain monitoring agent."""
    # Input data
    shipment_id: int
    current_temperature: float
    current_humidity: float
    current_lat: float
    current_lng: float
    spoilage_hours: Optional[float]
    tick: int

    # Agent working state
    anomaly_detected: bool
    risk_level: str  # "low", "medium", "high", "critical"
    risk_assessment: str
    nearby_warehouses: list[dict]
    recommended_warehouse: Optional[dict]
    reroute_proposal: str

    # Human-in-the-loop
    human_decision: Optional[str]  # "approved" or "rejected"
    alert_id: Optional[int]
    thread_id: Optional[str]

    # Output
    report_generated: bool
    report_id: Optional[int]
    messages: Annotated[list, add_messages]
