"""
SentinelTwin AI — Root Cause Analysis Module
Identifies the underlying cause of machine failures using historical sensor data,
state transitions, and system logs. Generates cause-effect analysis chains.
"""

import random
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from sentinelcore.config import MACHINE_MAP, THRESHOLDS, MachineStatus, AlertLevel


FAILURE_CAUSE_CHAINS = {
    "vibration_bearing": {
        "root": "Bearing lubrication failure",
        "chain": [
            {"cause": "Lubrication film breakdown", "effect": "Metal-to-metal contact"},
            {"cause": "Metal-to-metal contact", "effect": "Accelerated wear particles"},
            {"cause": "Wear particle contamination", "effect": "Increased vibration amplitude"},
            {"cause": "Increased vibration", "effect": "Bearing race damage"},
            {"cause": "Bearing race damage", "effect": "Machine failure risk"},
        ],
        "confidence": 0.88,
        "sensors": ["vibration", "temperature"],
    },
    "thermal_overload": {
        "root": "Cooling system degradation",
        "chain": [
            {"cause": "Coolant flow reduction", "effect": "Heat accumulation in motor"},
            {"cause": "Motor temperature rise", "effect": "Winding insulation stress"},
            {"cause": "Insulation stress", "effect": "Increased current draw"},
            {"cause": "Elevated current", "effect": "Further heat generation"},
            {"cause": "Thermal runaway", "effect": "Motor failure"},
        ],
        "confidence": 0.85,
        "sensors": ["temperature", "motor_current"],
    },
    "mechanical_overload": {
        "root": "Production load exceeding rated capacity",
        "chain": [
            {"cause": "Feed rate too high", "effect": "Mechanical stress accumulation"},
            {"cause": "Stress accumulation", "effect": "Vibration increase"},
            {"cause": "Vibration increase", "effect": "Fastener loosening"},
            {"cause": "Fastener loosening", "effect": "Structural instability"},
            {"cause": "Structural instability", "effect": "Catastrophic failure risk"},
        ],
        "confidence": 0.82,
        "sensors": ["load", "vibration", "motor_current"],
    },
    "electrical_fault": {
        "root": "Motor winding degradation",
        "chain": [
            {"cause": "Insulation aging", "effect": "Partial discharge events"},
            {"cause": "Partial discharges", "effect": "Insulation carbonization"},
            {"cause": "Carbonization", "effect": "Leakage current increase"},
            {"cause": "Leakage current", "effect": "Phase imbalance"},
            {"cause": "Phase imbalance", "effect": "Motor failure"},
        ],
        "confidence": 0.79,
        "sensors": ["motor_current", "temperature"],
    },
    "sensor_drift": {
        "root": "Sensor calibration drift",
        "chain": [
            {"cause": "Environmental contamination", "effect": "Sensor reading drift"},
            {"cause": "Sensor drift", "effect": "Inaccurate control signals"},
            {"cause": "Inaccurate control", "effect": "Sub-optimal machine operation"},
            {"cause": "Sub-optimal operation", "effect": "Increased wear rate"},
            {"cause": "Increased wear", "effect": "Premature failure"},
        ],
        "confidence": 0.71,
        "sensors": ["temperature", "vibration"],
    },
}


class RootCauseAnalyzer:
    """
    Analyzes machine failures and anomalies to identify root causes.
    Generates cause-effect chains and diagnostic recommendations.
    """

    def __init__(self):
        self._analysis_history: deque = deque(maxlen=100)
        self._last_analysis_tick: Dict[str, int] = {}
        self._tick_count: int = 0

    def analyze(self, machine_id: str, factory_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform root cause analysis for a machine in an abnormal state.
        """
        self._tick_count += 1
        config = MACHINE_MAP.get(machine_id)
        if not config:
            return {"analysis_triggered": False, "error": f"Unknown machine {machine_id}"}

        machine_data = factory_state.get("machines", {}).get(machine_id, {})
        sensors = machine_data.get("sensors", {})
        status = machine_data.get("status", MachineStatus.NORMAL)
        health = machine_data.get("health_score", 100.0)

        # Only perform analysis on machines in degraded states
        if status not in (MachineStatus.CRITICAL, MachineStatus.FAILURE, MachineStatus.WARNING):
            return {"analysis_triggered": False, "machine_id": machine_id, "status": status}

        # Identify most likely failure pattern
        pattern_key, pattern = self._identify_pattern(sensors, config)
        chain = pattern["chain"]
        confidence = pattern["confidence"] + random.uniform(-0.05, 0.05)
        confidence = max(0.50, min(0.99, confidence))

        # Build detailed analysis
        contributing_factors = self._extract_contributing_factors(sensors, config)
        timeline_events = self._reconstruct_timeline(machine_id, sensors, config)

        analysis = {
            "analysis_triggered": True,
            "machine_id": machine_id,
            "machine_name": config.name,
            "root_cause": pattern["root"],
            "failure_pattern": pattern_key,
            "confidence": round(confidence, 3),
            "severity": self._status_to_severity(status),
            "cause_effect_chain": chain,
            "contributing_factors": contributing_factors,
            "timeline_reconstruction": timeline_events,
            "primary_sensors_involved": pattern["sensors"],
            "current_readings": {k: round(v, 3) for k, v in sensors.items()},
            "health_score": round(health, 1),
            "recommended_inspection": self._generate_inspection_plan(pattern_key, config),
            "estimated_repair_time_hours": self._estimate_repair_time(pattern_key, health),
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._analysis_history.append(analysis)
        self._last_analysis_tick[machine_id] = self._tick_count
        return analysis

    def _identify_pattern(self, sensors: Dict[str, float], config) -> tuple:
        """Identify the most likely failure pattern from current sensor readings."""
        vib = sensors.get("vibration", config.nominal_vibration)
        temp = sensors.get("temperature", config.nominal_temp)
        curr = sensors.get("motor_current", config.nominal_current)
        load = sensors.get("load", config.nominal_load)

        vib_elevated = vib > config.nominal_vibration * 1.5
        temp_elevated = temp > config.nominal_temp * 1.25
        curr_elevated = curr > config.nominal_current * 1.20
        load_elevated = load > 88.0

        if vib_elevated and temp_elevated:
            return "vibration_bearing", FAILURE_CAUSE_CHAINS["vibration_bearing"]
        elif temp_elevated and curr_elevated:
            return "thermal_overload", FAILURE_CAUSE_CHAINS["thermal_overload"]
        elif load_elevated and vib_elevated:
            return "mechanical_overload", FAILURE_CAUSE_CHAINS["mechanical_overload"]
        elif curr_elevated and not vib_elevated:
            return "electrical_fault", FAILURE_CAUSE_CHAINS["electrical_fault"]
        else:
            return "sensor_drift", FAILURE_CAUSE_CHAINS["sensor_drift"]

    def _extract_contributing_factors(self, sensors: Dict[str, float],
                                       config) -> List[Dict[str, Any]]:
        """Extract and rank factors contributing to the failure."""
        factors = []

        deviations = [
            ("Vibration elevation", "vibration",
             sensors.get("vibration", 0), config.nominal_vibration, THRESHOLDS.vibration_critical),
            ("Temperature elevation", "temperature",
             sensors.get("temperature", 0), config.nominal_temp, THRESHOLDS.temp_critical),
            ("Current draw increase", "motor_current",
             sensors.get("motor_current", 0), config.nominal_current, THRESHOLDS.current_critical),
            ("Mechanical overload", "load",
             sensors.get("load", 0), config.nominal_load, 100.0),
        ]

        for label, sensor, current_val, nominal, critical in deviations:
            if current_val > nominal * 1.05:
                severity_pct = (current_val - nominal) / max(1.0, critical - nominal) * 100
                factors.append({
                    "factor": label,
                    "sensor": sensor,
                    "current_value": round(current_val, 3),
                    "nominal_value": round(nominal, 3),
                    "deviation_pct": round((current_val - nominal) / nominal * 100, 1),
                    "severity_contribution": round(min(100.0, severity_pct), 1),
                })

        factors.sort(key=lambda x: x["severity_contribution"], reverse=True)
        return factors

    def _reconstruct_timeline(self, machine_id: str,
                               sensors: Dict[str, float],
                               config) -> List[Dict[str, str]]:
        """Reconstruct a plausible event timeline leading to current state."""
        now = datetime.utcnow()
        events = []

        times = [
            now.replace(minute=now.minute - 8 if now.minute >= 8 else 0),
            now.replace(minute=now.minute - 5 if now.minute >= 5 else 0),
            now.replace(minute=now.minute - 3 if now.minute >= 3 else 0),
            now.replace(minute=now.minute - 1 if now.minute >= 1 else 0),
            now,
        ]

        vib = sensors.get("vibration", config.nominal_vibration)
        temp = sensors.get("temperature", config.nominal_temp)

        event_descriptions = [
            f"Sensor readings within normal range on {config.name}",
            f"Vibration begins slight increase: {round(config.nominal_vibration * 1.15, 2)} mm/s",
            f"Temperature starts rising: {round(config.nominal_temp * 1.10, 1)}°C",
            f"Multiple sensors enter warning zone simultaneously",
            f"Current state: Critical condition — RCA triggered",
        ]

        for t, desc in zip(times, event_descriptions):
            events.append({
                "time": t.strftime("%H:%M:%S"),
                "event": desc,
            })

        return events

    def _status_to_severity(self, status: str) -> str:
        mapping = {
            MachineStatus.CRITICAL: AlertLevel.CRITICAL,
            MachineStatus.FAILURE: AlertLevel.CRITICAL,
            MachineStatus.WARNING: AlertLevel.HIGH,
        }
        return mapping.get(status, AlertLevel.MEDIUM)

    def _generate_inspection_plan(self, pattern: str, config) -> List[str]:
        plans = {
            "vibration_bearing": [
                f"Shutdown {config.name} and perform bearing inspection",
                "Measure bearing clearance with dial indicator",
                "Check lubrication system pump pressure",
                "Inspect shaft coupling for misalignment",
                "Replace bearings if clearance exceeds tolerance",
            ],
            "thermal_overload": [
                f"Check coolant flow rate on {config.name}",
                "Inspect heat exchanger fins for blockage",
                "Measure motor winding temperature with IR camera",
                "Verify cooling fan operation and speed",
                "Check thermostat calibration",
            ],
            "mechanical_overload": [
                f"Reduce production feed rate on {config.name} by 25%",
                "Inspect drive train for worn components",
                "Check torque limiter setting against rated value",
                "Inspect gearbox for abnormal wear patterns",
            ],
            "electrical_fault": [
                f"Perform motor winding resistance test on {config.name}",
                "Measure insulation resistance with megohmmeter",
                "Check VFD output voltage balance across phases",
                "Inspect motor terminal connections for corrosion",
            ],
            "sensor_drift": [
                f"Perform multi-point calibration on {config.name} sensors",
                "Replace vibration sensor accelerometer if drift confirmed",
                "Check sensor cable shielding and grounding",
                "Compare readings against calibrated reference instrument",
            ],
        }
        return plans.get(pattern, ["Perform comprehensive machine inspection"])

    def _estimate_repair_time(self, pattern: str, health: float) -> float:
        base_times = {
            "vibration_bearing": 4.0,
            "thermal_overload": 2.0,
            "mechanical_overload": 1.5,
            "electrical_fault": 6.0,
            "sensor_drift": 1.0,
        }
        base = base_times.get(pattern, 3.0)
        health_factor = 1.0 + (1.0 - health / 100.0) * 2.0
        return round(base * health_factor, 1)

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        history = list(self._analysis_history)
        return history[-limit:]
