"""
SentinelTwin AI — Factory Efficiency Score Module
Computes a unified factory performance KPI from multiple operational metrics.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from sentinelcore.config import MACHINES, MachineStatus


class EfficiencyScorer:
    """Computes the Factory Efficiency Score — a single 0-100% operational KPI."""

    def __init__(self):
        self._latest: Optional[Dict] = None

    def compute(self, factory_state: Dict[str, Any]) -> Dict[str, Any]:
        machines = factory_state.get("machines", {})
        factory = factory_state.get("factory", {})

        # 1. Machine utilization (avg load across all normal machines)
        loads = []
        for mid, mdata in machines.items():
            status = mdata.get("status", "normal")
            if status not in (MachineStatus.OFFLINE, MachineStatus.FAILURE):
                loads.append(min(100.0, mdata.get("sensors", {}).get("load", 70.0)))
        utilization = sum(loads) / len(loads) if loads else 0.0
        # Ideal utilization is ~80%, penalize both over and under
        utilization_score = max(0.0, 100.0 - abs(utilization - 80.0) * 1.2)

        # 2. Production throughput score
        throughput = factory.get("current_throughput", 85.0)
        throughput_score = min(100.0, throughput)

        # 3. Downtime percentage
        down_count = sum(
            1 for mid, mdata in machines.items()
            if mdata.get("status") in (MachineStatus.FAILURE, MachineStatus.OFFLINE)
        )
        downtime_pct = (down_count / max(1, len(machines))) * 100.0
        downtime_score = max(0.0, 100.0 - downtime_pct * 10.0)

        # 4. Energy efficiency (inverse of average load deviation from optimal 75%)
        energy_deviations = []
        for mid, mdata in machines.items():
            load = mdata.get("sensors", {}).get("load", 75.0)
            energy_deviations.append(abs(load - 75.0))
        avg_energy_dev = sum(energy_deviations) / len(energy_deviations) if energy_deviations else 0.0
        energy_score = max(0.0, 100.0 - avg_energy_dev * 1.5)

        # 5. Failure risk score (inverse of average health degradation)
        health_scores = [mdata.get("health_score", 100.0) for mdata in machines.values()]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 100.0
        failure_risk_score = avg_health

        # Determine failure risk label
        if avg_health >= 80:
            failure_risk_label = "Low"
        elif avg_health >= 55:
            failure_risk_label = "Medium"
        elif avg_health >= 35:
            failure_risk_label = "High"
        else:
            failure_risk_label = "Critical"

        # Weighted composite score
        composite = (
            utilization_score * 0.20
            + throughput_score * 0.30
            + downtime_score * 0.25
            + energy_score * 0.15
            + failure_risk_score * 0.10
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        result = {
            "factory_efficiency_score": composite,
            "components": {
                "machine_utilization": round(utilization_score, 1),
                "production_throughput": round(throughput_score, 1),
                "downtime_score": round(downtime_score, 1),
                "energy_efficiency": round(energy_score, 1),
                "failure_risk_score": round(failure_risk_score, 1),
            },
            "raw_metrics": {
                "avg_utilization_pct": round(utilization, 1),
                "current_throughput": round(throughput, 2),
                "machines_down": down_count,
                "avg_health_score": round(avg_health, 1),
                "failure_risk": failure_risk_label,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._latest = result
        return result

    def get_latest(self) -> Optional[Dict[str, Any]]:
        return self._latest
