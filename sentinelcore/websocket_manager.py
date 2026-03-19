"""
SentinelTwin AI — WebSocket Connection Manager
Dual-pool: Dashboard 1 (/ws) and Dashboard 2 (/ws/d2).
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Dashboard 1 pool
        self.active_connections:  List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Dashboard 2 pool
        self.d2_connections: List[WebSocket] = []
        self.d2_metadata:    Dict[WebSocket, Dict] = {}
        self._lock = asyncio.Lock()

    # ── Dashboard 1 ───────────────────────────────────────────────────────────
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            self.connection_metadata[websocket] = {
                "client_id":    client_id or f"client_{len(self.active_connections)}",
                "connected_at": datetime.utcnow().isoformat(),
                "message_count": 0,
            }
        logger.info(f"WS connected: {self.connection_metadata[websocket]['client_id']} | Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                meta = self.connection_metadata.pop(websocket, {})
                logger.info(f"WS disconnected: {meta.get('client_id','unknown')} | Remaining: {len(self.active_connections)}")

    # ── Dashboard 2 ───────────────────────────────────────────────────────────
    async def connect_d2(self, websocket: WebSocket, client_id: Optional[str] = None) -> None:
        await websocket.accept()
        async with self._lock:
            self.d2_connections.append(websocket)
            self.d2_metadata[websocket] = {
                "client_id":    client_id or f"d2_{len(self.d2_connections)}",
                "connected_at": datetime.utcnow().isoformat(),
                "message_count": 0,
            }
        logger.info(f"D2 WS connected: {self.d2_metadata[websocket]['client_id']}")

    async def disconnect_d2(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.d2_connections:
                self.d2_connections.remove(websocket)
                meta = self.d2_metadata.pop(websocket, {})
                logger.info(f"D2 WS disconnected: {meta.get('client_id','unknown')}")

    async def broadcast_d2(self, payload: Dict[str, Any]) -> None:
        if not self.d2_connections:
            return
        text = json.dumps(payload)
        dead = []
        for ws in self.d2_connections.copy():
            try:
                await ws.send_text(text)
                if ws in self.d2_metadata:
                    self.d2_metadata[ws]["message_count"] += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect_d2(ws)

    # ── Shared ────────────────────────────────────────────────────────────────
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_text(json.dumps(message))
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["message_count"] += 1
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return
        text = json.dumps(message)
        dead = []
        for ws in self.active_connections.copy():
            try:
                await ws.send_text(text)
                if ws in self.connection_metadata:
                    self.connection_metadata[ws]["message_count"] += 1
            except WebSocketDisconnect:
                dead.append(ws)
            except RuntimeError as e:
                logger.warning(f"WS send error: {e}")
                dead.append(ws)
            except Exception as e:
                logger.error(f"Unexpected WS error: {e}")
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        await self.broadcast({"type": event_type, "timestamp": datetime.utcnow().isoformat(), "data": data})

    async def broadcast_sensor_update(self, factory_state: Dict[str, Any]) -> None:
        await self.broadcast_event("sensor_update", factory_state)

    async def broadcast_alert(self, alert: Dict[str, Any]) -> None:
        await self.broadcast_event("alert", alert)

    async def broadcast_anomaly(self, anomaly: Dict[str, Any]) -> None:
        await self.broadcast_event("anomaly_detected", anomaly)

    async def broadcast_prediction(self, prediction: Dict[str, Any]) -> None:
        await self.broadcast_event("predictive_maintenance", prediction)

    async def broadcast_cyber_threat(self, threat: Dict[str, Any]) -> None:
        await self.broadcast_event("cyber_threat", threat)

    async def broadcast_self_healing(self, action: Dict[str, Any]) -> None:
        await self.broadcast_event("self_healing_action", action)

    async def broadcast_defect(self, defect: Dict[str, Any]) -> None:
        await self.broadcast_event("defect_detected", defect)

    async def broadcast_scenario(self, scenario: Dict[str, Any]) -> None:
        await self.broadcast_event("scenario_update", scenario)

    async def broadcast_incident(self, incident: Dict[str, Any]) -> None:
        await self.broadcast_event("incident_timeline", incident)

    async def broadcast_efficiency_score(self, score: Dict[str, Any]) -> None:
        await self.broadcast_event("efficiency_score", score)

    async def broadcast_root_cause(self, analysis: Dict[str, Any]) -> None:
        await self.broadcast_event("root_cause_analysis", analysis)

    async def broadcast_optimization(self, recommendation: Dict[str, Any]) -> None:
        await self.broadcast_event("production_optimization", recommendation)

    async def broadcast_cyber_response(self, response: Dict[str, Any]) -> None:
        await self.broadcast_event("cyber_response", response)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        return {
            "dashboard1_connections": len(self.active_connections),
            "dashboard2_connections": len(self.d2_connections),
            "connections": [
                {"client_id": meta.get("client_id"), "connected_at": meta.get("connected_at"),
                 "message_count": meta.get("message_count", 0)}
                for meta in self.connection_metadata.values()
            ],
        }


manager = ConnectionManager()
