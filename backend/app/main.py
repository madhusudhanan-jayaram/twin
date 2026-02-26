"""FastAPI entry point + startup simulation loop."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.api.routes import router
from app.api.websocket import manager
from app.simulator.sensors import simulator
from app.agent.graph import run_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")

    # Wire simulator callbacks
    async def on_sensor_event(event_type: str, data: dict):
        if event_type == "sensor_update":
            await manager.broadcast("sensor_update", data)
        elif event_type == "trigger_agent":
            logger.info("Agent triggered by sensor anomaly")
            asyncio.create_task(run_agent(data))
        elif event_type == "report_ready":
            from app.agent.graph import _generate_and_broadcast_report
            asyncio.create_task(_generate_and_broadcast_report(data["shipment_id"]))

    simulator.on_update(on_sensor_event)

    yield


app = FastAPI(
    title="Cold Chain Integrity Demo",
    description="Predictive Cold Chain Monitoring with Agentic AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
