"""
SentinelTwin AI — AI Incident Timeline Module
Records all factory events in chronological order for complete operational traceability.
"""
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional


class IncidentTimeline:
    """Chronological event recorder for all factory incidents and AI actions."""

    EVENT_ICONS = {
        "anomaly": "⚠️",
        "predictive_alert": "🔮",
        "defect": "🔍",
        "cyber_threat": "🛡️",
        "self_healing": "♻️",
        "production_optimization": "📈",
        "scenario": "🎭",
        "machine_failure": "❌",
        "machine_recovery": "✅",
        "cyber_response": "🔒",
        "root_cause": "🧬",
        "info": "ℹ️",
    }

    def __init__(self):
        self._events: deque = deque(maxlen=1000)
        self._event_counter: int = 0

    def add_event(
        self,
        event_type: str,
        description: str,
        severity: str = "info",
        machine_id: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        self._event_counter += 1
        now = datetime.utcnow()
        event = {
            "event_id": f"EVT-{self._event_counter:05d}",
            "event_type": event_type,
            "icon": self.EVENT_ICONS.get(event_type, "📌"),
            "description": description,
            "severity": severity,
            "machine_id": machine_id,
            "timestamp": now.isoformat(),
            "time_display": now.strftime("%H:%M:%S"),
            "extra_data": extra_data or {},
        }
        self._events.append(event)
        return event

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = list(self._events)
        return list(reversed(events))[:limit]

    def get_total_count(self) -> int:
        return self._event_counter

    def clear(self) -> None:
        self._events.clear()
        self._event_counter = 0

    def get_by_machine(self, machine_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        events = [e for e in self._events if e.get("machine_id") == machine_id]
        return list(reversed(events))[:limit]

    def get_by_severity(self, severity: str, limit: int = 50) -> List[Dict[str, Any]]:
        events = [e for e in self._events if e.get("severity") == severity]
        return list(reversed(events))[:limit]
