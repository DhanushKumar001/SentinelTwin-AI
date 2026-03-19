"""
SentinelTwin AI — Dashboard 2 API Routes
REST endpoints + dedicated /ws/d2 WebSocket for the AI Control Dashboard.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from sentinelcore.websocket_manager import manager

logger = logging.getLogger(__name__)

d2_router    = APIRouter(prefix="/api/d2", tags=["Dashboard 2"])
d2_ws_router = APIRouter(tags=["Dashboard 2 WebSocket"])


@d2_router.get("/state")
async def get_d2_state(request: Request) -> Dict[str, Any]:
    engine = getattr(request.app.state, "d2_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Dashboard 2 engine not ready")
    return {
        "log":       engine.get_full_log(100),
        "ai_panel":  engine.get_ai_panel(),
        "response":  engine.get_response_panel(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@d2_router.get("/log")
async def get_log(request: Request, since: int = 0, limit: int = 100):
    engine = getattr(request.app.state, "d2_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Dashboard 2 engine not ready")
    entries = engine.get_log_since(since) if since > 0 else engine.get_full_log(limit)
    return {"entries": entries, "count": len(entries)}


@d2_router.get("/ai-panel")
async def get_ai_panel(request: Request):
    engine = getattr(request.app.state, "d2_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Dashboard 2 engine not ready")
    return {"machines": engine.get_ai_panel(), "timestamp": datetime.utcnow().isoformat()}


@d2_router.get("/response-panel")
async def get_response_panel(request: Request):
    engine = getattr(request.app.state, "d2_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Dashboard 2 engine not ready")
    return engine.get_response_panel()


@d2_router.delete("/log/clear")
async def clear_log(request: Request):
    engine = getattr(request.app.state, "d2_engine", None)
    if engine:
        engine.log.clear()
    return {"status": "cleared", "timestamp": datetime.utcnow().isoformat()}


@d2_ws_router.websocket("/ws/d2")
async def dashboard2_websocket(websocket: WebSocket):
    """Dedicated WebSocket for Dashboard 2 — streams d2_tick every 2 seconds."""
    client_id = f"d2_{id(websocket)}"
    await manager.connect_d2(websocket, client_id)
    try:
        await manager.send_personal_message(
            {"type": "d2_connected", "timestamp": datetime.utcnow().isoformat(),
             "data": {"client_id": client_id, "message": "Connected to SentinelTwin Dashboard 2",
                      "version": "2.0.0", "tick_interval": 2.0}},
            websocket,
        )
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                        websocket,
                    )
            except asyncio.TimeoutError:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await manager.send_personal_message(
                        {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()},
                        websocket,
                    )
                else:
                    break
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"D2 WebSocket error: {e}", exc_info=True)
    finally:
        await manager.disconnect_d2(websocket)
