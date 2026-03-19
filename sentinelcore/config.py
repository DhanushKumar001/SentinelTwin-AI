"""
SentinelTwin AI — Global Configuration
Centralized settings for the entire platform.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MachineConfig:
    machine_id: str
    name: str
    machine_type: str
    nominal_temp: float
    nominal_vibration: float
    nominal_current: float
    nominal_speed: float
    nominal_load: float
    production_rate_nominal: float
    installation_date: str
    runtime_hours_initial: float


@dataclass
class ThresholdConfig:
    temp_warning: float = 75.0
    temp_critical: float = 90.0
    vibration_warning: float = 7.0
    vibration_critical: float = 10.0
    current_warning: float = 80.0
    current_critical: float = 95.0
    load_warning: float = 80.0
    load_critical: float = 95.0
    anomaly_score_warning: float = 0.6
    anomaly_score_critical: float = 0.85
    failure_prob_warning: float = 0.5
    failure_prob_critical: float = 0.80


@dataclass
class SimulationConfig:
    tick_interval: float = 2.0
    sensor_noise_factor: float = 0.02
    degradation_rate: float = 0.001
    self_heal_delay: int = 15
    scenario_resolve_delay: int = 30
    history_length: int = 100
    predictive_window: int = 50


@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    log_level: str = "info"
    factory_name: str = "SentinelTwin Smart Factory"
    websocket_heartbeat: int = 30


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY MACHINE DEFINITIONS
# Five machines operating in sequence on the production line.
# ─────────────────────────────────────────────────────────────────────────────

MACHINES: List[MachineConfig] = [
    MachineConfig(
        machine_id="M1",
        name="Raw Material Processor",
        machine_type="processor",
        nominal_temp=62.0,
        nominal_vibration=3.5,
        nominal_current=65.0,
        nominal_speed=1450.0,
        nominal_load=70.0,
        production_rate_nominal=95.0,
        installation_date="2021-03-15",
        runtime_hours_initial=14200.0,
    ),
    MachineConfig(
        machine_id="M2",
        name="Assembly Robot",
        machine_type="robot",
        nominal_temp=55.0,
        nominal_vibration=2.8,
        nominal_current=58.0,
        nominal_speed=1200.0,
        nominal_load=65.0,
        production_rate_nominal=92.0,
        installation_date="2020-11-20",
        runtime_hours_initial=18500.0,
    ),
    MachineConfig(
        machine_id="M3",
        name="Quality Inspection Machine",
        machine_type="inspection",
        nominal_temp=48.0,
        nominal_vibration=1.5,
        nominal_current=45.0,
        nominal_speed=800.0,
        nominal_load=55.0,
        production_rate_nominal=98.0,
        installation_date="2022-01-10",
        runtime_hours_initial=9800.0,
    ),
    MachineConfig(
        machine_id="M4",
        name="Packaging Machine",
        machine_type="packaging",
        nominal_temp=52.0,
        nominal_vibration=4.2,
        nominal_current=72.0,
        nominal_speed=1800.0,
        nominal_load=75.0,
        production_rate_nominal=90.0,
        installation_date="2021-07-05",
        runtime_hours_initial=12600.0,
    ),
    MachineConfig(
        machine_id="M5",
        name="Distribution Robot",
        machine_type="robot",
        nominal_temp=50.0,
        nominal_vibration=3.0,
        nominal_current=60.0,
        nominal_speed=1100.0,
        nominal_load=60.0,
        production_rate_nominal=94.0,
        installation_date="2022-05-18",
        runtime_hours_initial=7400.0,
    ),
]

MACHINE_MAP: Dict[str, MachineConfig] = {m.machine_id: m for m in MACHINES}

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL SINGLETON INSTANCES
# ─────────────────────────────────────────────────────────────────────────────

THRESHOLDS = ThresholdConfig(
    temp_warning=float(os.getenv("TEMP_WARNING_THRESHOLD", 75.0)),
    temp_critical=float(os.getenv("TEMP_CRITICAL_THRESHOLD", 90.0)),
    vibration_warning=float(os.getenv("VIBRATION_WARNING_THRESHOLD", 7.0)),
    vibration_critical=float(os.getenv("VIBRATION_CRITICAL_THRESHOLD", 10.0)),
    current_warning=float(os.getenv("CURRENT_WARNING_THRESHOLD", 80.0)),
    current_critical=float(os.getenv("CURRENT_CRITICAL_THRESHOLD", 95.0)),
)

SIMULATION = SimulationConfig(
    tick_interval=float(os.getenv("SIMULATION_TICK_INTERVAL", 2.0)),
)

APP = AppConfig(
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", 8000)),
    env=os.getenv("ENV", "development"),
    log_level=os.getenv("LOG_LEVEL", "info"),
)

# ─────────────────────────────────────────────────────────────────────────────
# MACHINE STATE CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

class MachineStatus:
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILURE = "failure"
    HEALING = "healing"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class AlertLevel:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScenarioType:
    HIGH_VIBRATION = "high_vibration"
    OVERHEATING = "overheating"
    MACHINE_BREAKDOWN = "machine_breakdown"
    DEFECTIVE_PRODUCT = "defective_product"
    CYBER_ATTACK = "cyber_attack"
    PRODUCTION_BOTTLENECK = "production_bottleneck"
    BEARING_WEAR = "bearing_wear"
    POWER_SURGE = "power_surge"


class CyberThreatType:
    COMMAND_INJECTION = "command_injection"
    NETWORK_FLOODING = "network_flooding"
    UNAUTHORIZED_CONTROL = "unauthorized_machine_control"
    PLC_OVERRIDE = "plc_override_attack"
    ABNORMAL_TRAFFIC = "abnormal_traffic_burst"


class AnomalyType:
    VIBRATION_SPIKE = "vibration_spike"
    TEMPERATURE_SURGE = "temperature_surge"
    CURRENT_ANOMALY = "current_anomaly"
    LOAD_ANOMALY = "load_anomaly"
    MULTIVARIATE = "multivariate_anomaly"


# ─────────────────────────────────────────────────────────────────────────────
# DEFECT TYPES FOR VISION AI
# ─────────────────────────────────────────────────────────────────────────────

DEFECT_TYPES = [
    "structural_damage",
    "surface_defect",
    "misalignment",
    "missing_component",
    "dimensional_error",
    "coating_defect",
    "assembly_error",
]

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE STATUS COLORS (used by digital twin)
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_COLORS = {
    MachineStatus.NORMAL: "#2196F3",    # blue
    MachineStatus.WARNING: "#FF9800",   # orange/yellow
    MachineStatus.CRITICAL: "#F44336",  # red
    MachineStatus.FAILURE: "#9C27B0",   # purple
    MachineStatus.HEALING: "#4CAF50",   # green
    MachineStatus.OFFLINE: "#607D8B",   # grey
    MachineStatus.MAINTENANCE: "#FF5722",  # deep orange
}

HEALTH_HEATMAP_COLORS = {
    "healthy": "#4CAF50",
    "warning": "#FF9800",
    "critical": "#F44336",
}
