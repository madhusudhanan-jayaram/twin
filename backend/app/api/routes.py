"""REST API routes for the cold chain demo."""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Shipment, SensorReading, Warehouse, Alert, ComplianceReport, HumanDecision
from app.simulator.sensors import simulator
from app.simulator.route import get_route_as_latlng_list
from app.api.websocket import manager
from app.db.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ---------- Shipment ----------

@router.get("/shipment")
async def get_shipment(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Shipment))
    shipment = result.scalars().first()
    if not shipment:
        raise HTTPException(404, "No shipment found")
    return shipment


@router.get("/shipment/readings")
async def get_readings(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(SensorReading).order_by(SensorReading.id)
    )
    return result.scalars().all()


# ---------- Route ----------

@router.get("/route")
async def get_route():
    return {"waypoints": get_route_as_latlng_list()}


# ---------- Warehouses ----------

@router.get("/warehouses")
async def get_warehouses(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Warehouse))
    return result.scalars().all()


# ---------- Alerts ----------

@router.get("/alerts")
async def get_alerts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Alert).order_by(Alert.id.desc()))
    return result.scalars().all()


# ---------- Approval ----------

class ApprovalRequest(BaseModel):
    decision: str  # "approved" or "rejected"


@router.post("/alerts/{alert_id}/approve")
async def approve_alert(alert_id: int, body: ApprovalRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(404, "Alert not found")

    alert.human_decision = HumanDecision(body.decision)
    await session.commit()

    # Resume the agent graph
    from app.agent.graph import resume_agent
    if alert.thread_id:
        asyncio.create_task(resume_agent(alert.thread_id, body.decision, alert))

    # Broadcast decision
    await manager.broadcast("approval_decision", {
        "alert_id": alert_id,
        "decision": body.decision,
    })

    return {"status": "ok", "decision": body.decision}


# ---------- Compliance Reports ----------

@router.get("/reports")
async def get_reports(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ComplianceReport).order_by(ComplianceReport.id.desc()))
    return result.scalars().all()


@router.get("/reports/{report_id}")
async def get_report(report_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ComplianceReport).where(ComplianceReport.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


# ---------- Simulation Control ----------

@router.post("/simulation/start")
async def start_simulation():
    if simulator.running:
        return {"status": "already_running"}

    async def run_sim():
        await simulator.run(async_session)

    asyncio.create_task(run_sim())
    return {"status": "started"}


@router.post("/simulation/stop")
async def stop_simulation():
    simulator.running = False
    return {"status": "stopped"}


@router.post("/simulation/reset")
async def reset_simulation(session: AsyncSession = Depends(get_session)):
    simulator.running = False
    simulator.reset()

    # Clear sensor readings and alerts
    from sqlmodel import delete
    await session.execute(delete(SensorReading))
    await session.execute(delete(Alert))
    await session.execute(delete(ComplianceReport))

    result = await session.execute(select(Shipment))
    shipment = result.scalars().first()
    if shipment:
        shipment.status = "in_transit"
        shipment.current_lat = 32.7767
        shipment.current_lng = -96.7970
        shipment.current_temperature = 4.0
        shipment.current_humidity = 45.0
        shipment.waypoint_index = 0
        shipment.predicted_spoilage_hours = None

    await session.commit()
    return {"status": "reset"}


@router.get("/simulation/status")
async def simulation_status():
    return {
        "running": simulator.running,
        "tick": simulator.tick,
        "temperature": simulator.temperature,
        "waypoint_index": simulator.waypoint_index,
    }
