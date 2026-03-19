"""
SentinelTwin AI — Machine Lifecycle Monitoring Module
Tracks long-term operational history, health trends, maintenance records,
and predicted remaining useful life for each machine.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sentinelcore.config import MACHINES, MACHINE_MAP


class LifecycleMonitor:
    """
    Tracks installation date, runtime hours, maintenance history,
    failure history, health score trends, and predicted remaining lifetime.
    """

    def __init__(self):
        self._lifecycle_data: Dict[str, Dict] = {}
        for m in MACHINES:
            config = MACHINE_MAP[m.machine_id]
            self._lifecycle_data[m.machine_id] = {
                "machine_id": m.machine_id,
                "machine_name": m.name,
                "installation_date": config.installation_date,
                "runtime_hours": config.runtime_hours_initial,
                "health_score": 100.0,
                "health_trend": [],
                "maintenance_history": self._generate_maintenance_history(config),
                "failure_history": [],
                "predicted_remaining_life_months": self._estimate_remaining_life(
                    config.runtime_hours_initial
                ),
                "last_maintenance_date": self._get_last_maintenance(config.installation_date),
                "next_maintenance_due": self._get_next_maintenance(config.runtime_hours_initial),
                "total_failures": 0,
                "total_maintenance_events": 3,
            }

    def _generate_maintenance_history(self, config) -> List[Dict]:
        """Generate plausible historical maintenance records."""
        base_date = datetime.strptime(config.installation_date, "%Y-%m-%d")
        records = []
        hours_step = config.runtime_hours_initial / 4
        for i in range(3):
            date = base_date + timedelta(days=int(hours_step * (i + 1) / 24))
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": ["Preventive", "Corrective", "Preventive"][i],
                "description": [
                    "Lubrication, filter replacement, calibration check",
                    "Bearing replacement — elevated vibration",
                    "Belt tensioning, thermal sensor recalibration",
                ][i],
                "technician": f"Tech-{(i % 3) + 1:02d}",
                "duration_hours": [2.5, 6.0, 3.0][i],
                "cost_usd": [450, 1200, 600][i],
            })
        return records

    def _estimate_remaining_life(self, runtime_hours: float) -> float:
        """Estimate remaining lifetime in months."""
        max_lifetime_hours = 25000.0
        remaining_hours = max(0.0, max_lifetime_hours - runtime_hours)
        return round(remaining_hours / (24 * 30), 1)

    def _get_last_maintenance(self, installation_date: str) -> str:
        base = datetime.strptime(installation_date, "%Y-%m-%d")
        last = base + timedelta(days=180)
        return last.strftime("%Y-%m-%d")

    def _get_next_maintenance(self, runtime_hours: float) -> str:
        next_due_hours = (runtime_hours // 2000 + 1) * 2000
        hours_until = max(0, next_due_hours - runtime_hours)
        days_until = hours_until / 24
        next_date = datetime.utcnow() + timedelta(days=days_until)
        return next_date.strftime("%Y-%m-%d")

    def update(self, factory_state: Dict[str, Any]) -> None:
        """Update lifecycle data from current factory state."""
        machines = factory_state.get("machines", {})
        for machine_id, machine_data in machines.items():
            if machine_id not in self._lifecycle_data:
                continue
            lc = self._lifecycle_data[machine_id]
            sensors = machine_data.get("sensors", {})
            health = machine_data.get("health_score", 100.0)
            status = machine_data.get("status", "normal")

            lc["runtime_hours"] = sensors.get("runtime_hours", lc["runtime_hours"])
            lc["health_score"] = round(health, 1)
            lc["predicted_remaining_life_months"] = self._estimate_remaining_life(
                lc["runtime_hours"]
            )
            lc["next_maintenance_due"] = self._get_next_maintenance(lc["runtime_hours"])

            # Track health trend (keep last 50 readings)
            trend = lc["health_trend"]
            trend.append(round(health, 1))
            if len(trend) > 50:
                lc["health_trend"] = trend[-50:]

            # Record failure events
            if status == "failure":
                if not lc["failure_history"] or lc["failure_history"][-1].get("resolved"):
                    lc["failure_history"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "active",
                        "resolved": False,
                    })
                    lc["total_failures"] += 1
            else:
                if lc["failure_history"] and not lc["failure_history"][-1].get("resolved"):
                    lc["failure_history"][-1]["resolved"] = True
                    lc["failure_history"][-1]["resolved_at"] = datetime.utcnow().isoformat()

    def get_lifecycle(self, machine_id: str) -> Optional[Dict[str, Any]]:
        return self._lifecycle_data.get(machine_id)

    def get_all_lifecycle(self) -> Dict[str, Any]:
        return dict(self._lifecycle_data)
