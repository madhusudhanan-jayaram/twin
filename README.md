# Cold Chain Digital Twin Demo

A real-time pharmaceutical cold chain monitoring system with an agentic AI that detects temperature anomalies, proposes reroutes, and generates FDA compliance reports — all with human-in-the-loop approval.

---

## Overview

This demo simulates a refrigerated drug shipment (Skyrizi) travelling from Dallas, TX to Oklahoma City. When the refrigeration unit fails mid-route, an AI agent automatically:

1. Detects the temperature anomaly
2. Assesses spoilage risk using a thermal model
3. Finds the nearest cold-storage warehouses
4. Proposes a reroute and waits for human approval
5. Executes the reroute (or logs rejection)
6. Generates an FDA-style compliance report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, LangGraph, LangChain, SQLModel, SQLite |
| AI | OpenAI GPT (via LangChain) |
| Frontend | React 19, Vite, Tailwind CSS, Recharts, React Leaflet |
| Real-time | WebSockets |
| Packaging | `uv` (Python), `npm` (Node) |

---

## Project Structure

```
cold-chain-demo/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph agent (graph, nodes, state, tools)
│   │   ├── api/            # FastAPI routes and WebSocket manager
│   │   ├── db/             # Database setup (SQLite + SQLModel)
│   │   ├── models/         # Pydantic/SQLModel schemas
│   │   ├── services/       # FDA report generation
│   │   ├── simulator/      # Sensor simulator, route, scenario, thermal model
│   │   ├── config.py       # Settings (loaded from .env)
│   │   └── main.py         # FastAPI app entry point
│   ├── .env                # Your local secrets (never committed)
│   ├── .env.example        # Template for required env vars
│   └── pyproject.toml      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # Dashboard, LiveMap, SensorCharts, AlertPanel, etc.
│   │   ├── hooks/          # useWebSocket hook
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── .gitignore
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- `uv` package manager — install with:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- An OpenAI API key

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/madhusudhanan-jayaram/twin.git
cd twin
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set your OpenAI key:

```env
COLD_CHAIN_OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Install backend dependencies

```bash
cd backend
uv sync
```

### 4. Install frontend dependencies

```bash
cd ../frontend
npm install
```

---

## Running Locally

Open **two terminal windows**.

### Terminal 1 — Backend

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`
Interactive API docs: `http://localhost:8000/docs`

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev -- --host
```

The dashboard will be available at: `http://localhost:5173`

---

## Running with Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## Configuration

All backend settings are controlled via environment variables prefixed with `COLD_CHAIN_`:

| Variable | Default | Description |
|---|---|---|
| `COLD_CHAIN_OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `COLD_CHAIN_DATABASE_URL` | `sqlite+aiosqlite:///./cold_chain.db` | Database URL |
| `COLD_CHAIN_SIMULATION_TICK_SECONDS` | `2.0` | Real seconds per simulation tick |
| `COLD_CHAIN_SIMULATION_MINUTES_PER_TICK` | `5.0` | Simulated minutes per tick |
| `COLD_CHAIN_TEMPERATURE_THRESHOLD_CELSIUS` | `6.0` | Temperature warning threshold |
| `COLD_CHAIN_CRITICAL_TEMPERATURE_CELSIUS` | `8.0` | Temperature that triggers the AI agent |
| `COLD_CHAIN_WAREHOUSE_SEARCH_RADIUS_MILES` | `50.0` | Radius for finding nearby warehouses |

---

## Demo Walkthrough

The simulation runs a scripted scenario automatically on startup:

| Phase | Ticks | What Happens |
|---|---|---|
| Normal transit | 0 – 44 | Truck leaves Dallas. Refrigeration nominal (~4°C). |
| Traffic delay | 45 – 52 | Congestion near Ardmore, OK. Speed drops, temp starts rising. |
| Partial failure | 53 – 59 | Refrigeration unit partially fails. Temp rising faster. |
| Critical / Agent triggered | 60+ | Temp exceeds 8°C threshold. AI agent activates. |
| Human approval | — | Dashboard shows reroute proposal. Approve or reject. |
| Reroute / Report | — | Truck reroutes to warehouse. FDA report generated. |

Each tick = 2 real seconds = 5 simulated minutes.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shipment` | Current shipment status |
| `GET` | `/api/shipment/readings` | All sensor readings |
| `GET` | `/api/route` | Route waypoints |
| `GET` | `/api/warehouses` | All warehouses |
| `GET` | `/api/alerts` | All alerts |
| `POST` | `/api/approve/{alert_id}` | Approve a reroute proposal |
| `POST` | `/api/reject/{alert_id}` | Reject a reroute proposal |
| `GET` | `/api/reports` | All compliance reports |
| `WebSocket` | `/ws` | Real-time sensor and agent events |

---

## Agent Flow (LangGraph)

```
detect_anomaly
      │
      ▼ (if anomaly)
  assess_risk
      │
      ▼
find_warehouses
      │
      ▼
 propose_reroute
      │
      ▼
 await_approval  ◄── human decision via dashboard
      │
   approved?
   ┌──┴──┐
  yes    no
   │      │
execute  log_rejection
_reroute
   │
   ▼
generate_report
```

---

## Security Notes

- The `backend/.env` file is listed in `.gitignore` and is **never committed to git**.
- Use `backend/.env.example` as a template when setting up on a new machine.
- Do not hardcode API keys in source files.
