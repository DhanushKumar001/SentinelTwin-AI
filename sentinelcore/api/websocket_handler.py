"""
SentinelTwin AI — WebSocket Handler
Handles real-time bidirectional communication with frontend clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from sentinelcore.websocket_manager import manager

logger = logging.getLogger(__name__)
ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time factory data streaming.
    Accepts connections from frontend clients and handles bidirectional messaging.
    """
    client_id = websocket.headers.get("X-Client-ID", f"browser_{id(websocket)}")
    await manager.connect(websocket, client_id=client_id)

    try:
        # Send initial connection confirmation with system info
        await manager.send_personal_message(
            {
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "client_id": client_id,
                    "message": "Connected to SentinelTwin AI Platform",
                    "server_version": "1.0.0",
                    "tick_interval": 2.0,
                },
            },
            websocket,
        )

        # Listen for incoming messages from the client
        while True:
            try:
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=60.0
                )
                await _handle_client_message(websocket, raw_message)

            except asyncio.TimeoutError:
                # Send a heartbeat ping to keep connection alive
                if websocket.client_state == WebSocketState.CONNECTED:
                    await manager.send_personal_message(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": {"status": "alive"},
                        },
                        websocket,
                    )
                else:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected normally.")
    except RuntimeError as e:
        logger.warning(f"WebSocket runtime error for {client_id}: {e}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}", exc_info=True)
    finally:
        await manager.disconnect(websocket)


async def _handle_client_message(websocket: WebSocket, raw_message: str) -> None:
    """
    Handle incoming messages from a WebSocket client.
    Supports commands: ping, subscribe, scenario_trigger, machine_command.
    """
    try:
        message = json.loads(raw_message)
        msg_type = message.get("type", "unknown")
        data = message.get("data", {})

        logger.debug(f"Received WebSocket message: type={msg_type}")

        if msg_type == "ping":
            await manager.send_personal_message(
                {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"latency": "ok"},
                },
                websocket,
            )

        elif msg_type == "request_state":
            # Client is requesting a full state snapshot
            await manager.send_personal_message(
                {
                    "type": "state_snapshot_requested",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"message": "State will arrive in next tick broadcast"},
                },
                websocket,
            )

        elif msg_type == "subscribe":
            # Client subscribing to specific event types
            event_types = data.get("events", [])
            await manager.send_personal_message(
                {
                    "type": "subscription_confirmed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"subscribed_to": event_types},
                },
                websocket,
            )

        elif msg_type == "client_info":
            # Client sending identification info
            logger.info(
                f"Client info received: {data.get('name', 'unknown')} "
                f"v{data.get('version', 'unknown')}"
            )

        else:
            logger.debug(f"Unhandled WebSocket message type: {msg_type}")

    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON received from client: {raw_message[:100]}")
        await manager.send_personal_message(
            {
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"error": "Invalid JSON format"},
            },
            websocket,
        )
    except Exception as e:
        logger.error(f"Error handling client message: {e}", exc_info=True)
