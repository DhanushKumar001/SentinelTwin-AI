"""
SentinelTwin AI — Smart Alert Prioritization Module
Intelligently categorizes, deduplicates, and prioritizes all factory alerts
to prevent alert overload and ensure operators focus on the most critical issues.
"""
import random
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
from sentinelcore.config import AlertLevel, MACHINE_MAP


class AlertPrioritizer:
    """
    Intelligent alert prioritization engine.
    Assigns severity levels, deduplicates near-duplicate alerts,
    and presents a ranked, actionable alert stream.
    """

    def __init__(self):
        self._alert_history: deque = deque(maxlen=500)
        self._active_alerts: Dict[str, Dict] = {}
        self._suppression_window_secs: float = 30.0
        self._alert_counter: int = 0
        self._last_alert_times: Dict[str, float] = {}

    def process_and_prioritize(
        self,
        anomalies: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        cyber_threats: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Aggregate alerts from all modules, deduplicate, prioritize, and return
        a sorted alert list with Critical first.
        """
        raw_alerts = []

        # Convert anomalies to alerts
        for anomaly in anomalies:
            raw_alerts.append(self._from_anomaly(anomaly))

        # Convert high-probability predictions to alerts
        for pred in predictions:
            if pred.get("failure_probability", 0) >= 0.50:
                raw_alerts.append(self._from_prediction(pred))

        # Convert cyber threats to alerts
        for threat in cyber_threats:
            raw_alerts.append(self._from_cyber_threat(threat))

        # Deduplicate by machine + type within suppression window
        deduplicated = self._deduplicate(raw_alerts)

        # Sort: Critical → High → Medium → Low
        priority_order = {
            AlertLevel.CRITICAL: 0,
            AlertLevel.HIGH: 1,
            AlertLevel.MEDIUM: 2,
            AlertLevel.LOW: 3,
            AlertLevel.INFO: 4,
        }
        deduplicated.sort(key=lambda a: priority_order.get(a.get("level", AlertLevel.LOW), 5))

        for alert in deduplicated:
            self._alert_history.append(alert)
            self._active_alerts[alert["alert_key"]] = alert

        return deduplicated

    def _from_anomaly(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        severity = anomaly.get("severity", AlertLevel.MEDIUM)
        machine_id = anomaly.get("machine_id", "unknown")
        config = MACHINE_MAP.get(machine_id)
        machine_name = config.name if config else machine_id
        self._alert_counter += 1
        return {
            "alert_id": f"ALT-{self._alert_counter:05d}",
            "alert_key": f"anomaly_{machine_id}_{anomaly.get('anomaly_type', '')}",
            "source": "Anomaly Detection AI",
            "type": "anomaly",
            "level": severity,
            "machine_id": machine_id,
            "machine_name": machine_name,
            "title": f"Anomaly Detected: {anomaly.get('anomaly_type', 'unknown').replace('_', ' ').title()}",
            "description": (
                f"{machine_name} showing {anomaly.get('anomaly_type','').replace('_',' ')} "
                f"(score: {anomaly.get('composite_score', 0):.2f})"
            ),
            "score": anomaly.get("composite_score", 0),
            "timestamp": anomaly.get("timestamp", datetime.utcnow().isoformat()),
            "acknowledged": False,
        }

    def _from_prediction(self, pred: Dict[str, Any]) -> Dict[str, Any]:
        prob = pred.get("failure_probability", 0)
        machine_id = pred.get("machine_id", "unknown")
        config = MACHINE_MAP.get(machine_id)
        machine_name = config.name if config else machine_id
        if prob >= 0.85:
            level = AlertLevel.CRITICAL
        elif prob >= 0.70:
            level = AlertLevel.HIGH
        elif prob >= 0.50:
            level = AlertLevel.MEDIUM
        else:
            level = AlertLevel.LOW
        self._alert_counter += 1
        return {
            "alert_id": f"ALT-{self._alert_counter:05d}",
            "alert_key": f"prediction_{machine_id}",
            "source": "Predictive Maintenance AI",
            "type": "predictive_maintenance",
            "level": level,
            "machine_id": machine_id,
            "machine_name": machine_name,
            "title": f"Failure Risk: {machine_name} — {prob*100:.0f}%",
            "description": pred.get("recommendation", "Maintenance recommended"),
            "score": prob,
            "rul_hours": pred.get("rul_hours", 0),
            "timestamp": pred.get("timestamp", datetime.utcnow().isoformat()),
            "acknowledged": False,
        }

    def _from_cyber_threat(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        self._alert_counter += 1
        machine_id = threat.get("target_machine", "network")
        return {
            "alert_id": f"ALT-{self._alert_counter:05d}",
            "alert_key": f"cyber_{machine_id}_{threat.get('threat_type','')}",
            "source": "Cybersecurity Intelligence",
            "type": "cyber_threat",
            "level": AlertLevel.CRITICAL,
            "machine_id": machine_id,
            "machine_name": threat.get("target_machine", "Network"),
            "title": f"Cyber Threat: {threat.get('threat_type','').replace('_',' ').title()}",
            "description": (
                f"Severity: {threat.get('severity','critical')} — "
                f"{threat.get('description','Malicious activity detected')}"
            ),
            "score": 1.0,
            "timestamp": threat.get("timestamp", datetime.utcnow().isoformat()),
            "acknowledged": False,
        }

    def _deduplicate(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove near-duplicate alerts within the suppression window."""
        seen_keys = set()
        result = []
        for alert in alerts:
            key = alert.get("alert_key", "")
            if key not in seen_keys:
                seen_keys.add(key)
                result.append(alert)
        return result

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self._alert_history)[-limit:]

    def acknowledge_alert(self, alert_id: str) -> bool:
        for key, alert in self._active_alerts.items():
            if alert.get("alert_id") == alert_id:
                alert["acknowledged"] = True
                return True
        return False
