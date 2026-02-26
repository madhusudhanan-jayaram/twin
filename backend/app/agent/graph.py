"""LangGraph StateGraph with interrupt() for human approval."""

import logging
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from app.agent.state import ColdChainAgentState
from app.agent.nodes import (
    detect_anomaly,
    assess_risk,
    find_warehouses,
    propose_reroute,
    execute_reroute,
    generate_report,
    log_rejection,
)
from app.api.websocket import manager
from app.db.database import async_session
from app.models import Alert, AlertSeverity, HumanDecision, ComplianceReport, Disposition, ShipmentStatus, Shipment, Warehouse
from app.simulator.sensors import simulator
from app.services.fda_report import generate_fda_report

from sqlmodel import select

logger = logging.getLogger(__name__)

checkpointer = MemorySaver()


def should_continue_after_detect(state: ColdChainAgentState) -> str:
    if state.get("anomaly_detected"):
        return "assess_risk"
    return END


async def await_approval(state: ColdChainAgentState) -> dict:
    """Interrupt the graph and wait for human approval."""
    wh = state.get("recommended_warehouse")
    proposal = state.get("reroute_proposal", "")

    # Create alert in DB
    async with async_session() as session:
        alert = Alert(
            shipment_id=state["shipment_id"],
            alert_type="reroute_proposal",
            severity=AlertSeverity.critical,
            message=proposal,
            ai_recommendation=proposal,
            proposed_warehouse_id=wh["id"] if wh else None,
            proposed_warehouse_name=wh["name"] if wh else None,
            human_decision=HumanDecision.pending,
            thread_id=state.get("thread_id"),
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        alert_id = alert.id

    # Broadcast approval request to frontend
    await manager.broadcast("approval_request", {
        "alert_id": alert_id,
        "proposal": proposal,
        "warehouse": wh,
        "temperature": state["current_temperature"],
        "spoilage_hours": state.get("spoilage_hours"),
        "risk_level": state.get("risk_level", "high"),
    })

    # Interrupt and wait for human decision
    decision = interrupt({"alert_id": alert_id, "proposal": proposal})

    return {
        "human_decision": decision,
        "alert_id": alert_id,
        "messages": [{"role": "assistant", "content": f"Human decision received: {decision}"}],
    }


def route_after_approval(state: ColdChainAgentState) -> str:
    if state.get("human_decision") == "approved":
        return "execute_reroute"
    return "log_rejection"


# Build the graph
def build_graph():
    builder = StateGraph(ColdChainAgentState)

    builder.add_node("detect_anomaly", detect_anomaly)
    builder.add_node("assess_risk", assess_risk)
    builder.add_node("find_warehouses", find_warehouses)
    builder.add_node("propose_reroute", propose_reroute)
    builder.add_node("await_approval", await_approval)
    builder.add_node("execute_reroute", execute_reroute)
    builder.add_node("generate_report", generate_report)
    builder.add_node("log_rejection", log_rejection)

    builder.set_entry_point("detect_anomaly")

    builder.add_conditional_edges("detect_anomaly", should_continue_after_detect)
    builder.add_edge("assess_risk", "find_warehouses")
    builder.add_edge("find_warehouses", "propose_reroute")
    builder.add_edge("propose_reroute", "await_approval")
    builder.add_conditional_edges("await_approval", route_after_approval)
    builder.add_edge("execute_reroute", "generate_report")
    builder.add_edge("generate_report", END)
    builder.add_edge("log_rejection", END)

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()


async def run_agent(trigger_data: dict):
    """Run the agent when triggered by sensor anomaly."""
    thread_id = str(uuid.uuid4())

    # Also create warning alert
    async with async_session() as session:
        alert = Alert(
            shipment_id=trigger_data["shipment_id"],
            alert_type="temperature_critical",
            severity=AlertSeverity.critical,
            message=f"Temperature {trigger_data['temperature']}°C exceeds threshold. AI agent activated.",
            thread_id=thread_id,
        )
        session.add(alert)
        await session.commit()

    await manager.broadcast("alert", {
        "type": "temperature_critical",
        "severity": "critical",
        "message": f"Temperature {trigger_data['temperature']}°C exceeds threshold. AI agent activated.",
        "timestamp": datetime.utcnow().isoformat(),
    })

    initial_state: ColdChainAgentState = {
        "shipment_id": trigger_data["shipment_id"],
        "current_temperature": trigger_data["temperature"],
        "current_humidity": trigger_data["humidity"],
        "current_lat": trigger_data["lat"],
        "current_lng": trigger_data["lng"],
        "spoilage_hours": trigger_data.get("spoilage_hours"),
        "tick": trigger_data.get("tick", 0),
        "anomaly_detected": False,
        "risk_level": "low",
        "risk_assessment": "",
        "nearby_warehouses": [],
        "recommended_warehouse": None,
        "reroute_proposal": "",
        "human_decision": None,
        "alert_id": None,
        "thread_id": thread_id,
        "report_generated": False,
        "report_id": None,
        "messages": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        async for event in graph.astream(initial_state, config):
            logger.info(f"Agent event: {list(event.keys())}")
    except Exception as e:
        logger.error(f"Agent error: {e}")


async def resume_agent(thread_id: str, decision: str, alert: Alert):
    """Resume the agent after human approval/rejection."""
    config = {"configurable": {"thread_id": thread_id}}

    try:
        async for event in graph.astream(Command(resume=decision), config):
            logger.info(f"Agent resume event: {list(event.keys())}")

            # Check if reroute was executed
            if "execute_reroute" in event:
                wh = None
                # Get warehouse from alert
                if alert.proposed_warehouse_id:
                    async with async_session() as session:
                        result = await session.execute(
                            select(Warehouse).where(Warehouse.id == alert.proposed_warehouse_id)
                        )
                        wh = result.scalars().first()

                if wh:
                    simulator.start_reroute(wh.lat, wh.lng)

                    # Update shipment status
                    async with async_session() as session:
                        result = await session.execute(
                            select(Shipment).where(Shipment.id == alert.shipment_id)
                        )
                        shipment = result.scalars().first()
                        if shipment:
                            shipment.status = ShipmentStatus.rerouting
                            await session.commit()

                    await manager.broadcast("route_update", {
                        "type": "reroute",
                        "warehouse": {
                            "name": wh.name,
                            "lat": wh.lat,
                            "lng": wh.lng,
                            "city": wh.city,
                            "state": wh.state,
                        },
                        "from_lat": simulator.temperature,  # current position
                    })

            # Check if report should be generated
            if "generate_report" in event:
                await _generate_and_broadcast_report(alert.shipment_id)

    except Exception as e:
        logger.error(f"Agent resume error: {e}")


async def _generate_and_broadcast_report(shipment_id: int):
    """Generate FDA report and broadcast to frontend."""
    async with async_session() as session:
        # Get sensor readings
        result = await session.execute(
            select(SensorReading)
            .where(SensorReading.shipment_id == shipment_id)
            .order_by(SensorReading.id)
        )
        readings = result.scalars().all()

        result = await session.execute(select(Shipment).where(Shipment.id == shipment_id))
        shipment = result.scalars().first()

    temps = [r.temperature_celsius for r in readings]
    in_range = sum(1 for t in temps if 2.0 <= t <= 8.0)
    pct_in_range = (in_range / len(temps) * 100) if temps else 100.0

    excursions = []
    for r in readings:
        if r.temperature_celsius > 8.0:
            excursions.append(f"  {r.timestamp}: {r.temperature_celsius}°C")

    max_temp = max(temps) if temps else 0.0
    min_temp = min(temps) if temps else 0.0

    if pct_in_range >= 95:
        disposition = Disposition.PASS
    elif pct_in_range >= 80:
        disposition = Disposition.CONDITIONAL
    else:
        disposition = Disposition.FAIL

    # Generate report via Claude (or fallback)
    report_text = await generate_fda_report(
        drug_name="Skyrizi (risankizumab)",
        batch_number="SKZ-2024-0847",
        temps=temps,
        max_temp=max_temp,
        min_temp=min_temp,
        pct_in_range=pct_in_range,
        excursions=excursions,
        disposition=disposition.value,
    )

    async with async_session() as session:
        report = ComplianceReport(
            shipment_id=shipment_id,
            summary=f"Cold chain compliance report for Skyrizi batch SKZ-2024-0847",
            temperature_log_summary=f"{len(readings)} readings, range {min_temp:.1f}-{max_temp:.1f}°C",
            excursion_events="\n".join(excursions) if excursions else "None",
            total_time_in_range_percent=round(pct_in_range, 1),
            max_temperature_recorded=max_temp,
            min_temperature_recorded=min_temp,
            disposition=disposition,
            full_report=report_text,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)

        await manager.broadcast("report_ready", {
            "report_id": report.id,
            "disposition": disposition.value,
            "summary": report.summary,
            "pct_in_range": round(pct_in_range, 1),
        })
