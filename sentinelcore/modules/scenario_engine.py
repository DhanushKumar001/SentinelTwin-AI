"""
SentinelTwin AI — Scenario Simulation Engine
Manages and triggers factory event scenarios for demonstration and stress testing.
Supports multiple simultaneous scenarios with auto-resolve.
"""

import random
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sentinelcore.config import ScenarioType, CyberThreatType, MachineStatus, MACHINES

if TYPE_CHECKING:
    from sentinelcore.modules.factory_simulation import FactorySimulation


SCENARIO_DEFINITIONS = {
    ScenarioType.HIGH_VIBRATION: {
        "name": "High Vibration Alert",
        "description": "Machine vibration exceeds critical threshold — bearing wear pattern",
        "default_machine": "M2",
        "fault_injections": {"vibration": 2.5, "temperature": 1.3},
        "duration_ticks": 25,
        "auto_resolve": True,
    },
    ScenarioType.OVERHEATING: {
        "name": "Machine Overheating",
        "description": "Critical thermal condition — cooling system failure simulation",
        "default_machine": "M1",
        "fault_injections": {"temperature": 2.2, "motor_current": 1.4},
        "duration_ticks": 20,
        "auto_resolve": True,
    },
    ScenarioType.MACHINE_BREAKDOWN: {
        "name": "Machine Breakdown",
        "description": "Complete machine failure requiring immediate maintenance",
        "default_machine": "M4",
        "fault_injections": {"vibration": 3.5, "temperature": 2.8, "motor_current": 1.8},
        "duration_ticks": 30,
        "auto_resolve": True,
    },
    ScenarioType.DEFECTIVE_PRODUCT: {
        "name": "Defective Product Detection",
        "description": "Quality inspection detects high defect rate in production batch",
        "default_machine": "M3",
        "fault_injections": {"load": 1.3},
        "duration_ticks": 15,
        "auto_resolve": True,
    },
    ScenarioType.CYBER_ATTACK: {
        "name": "Cyber Attack Simulation",
        "description": "PLC override attack on production machine",
        "default_machine": "M3",
        "fault_injections": {"speed": 0.4, "load": 1.5},
        "duration_ticks": 20,
        "auto_resolve": True,
    },
    ScenarioType.PRODUCTION_BOTTLENECK: {
        "name": "Production Bottleneck",
        "description": "Upstream machine slowdown creating a production line bottleneck",
        "default_machine": "M2",
        "fault_injections": {"speed": 0.5, "load": 1.6},
        "duration_ticks": 20,
        "auto_resolve": True,
    },
    ScenarioType.BEARING_WEAR: {
        "name": "Bearing Wear Progression",
        "description": "Progressive bearing wear simulation with gradual sensor degradation",
        "default_machine": "M1",
        "fault_injections": {"vibration": 1.8, "temperature": 1.4, "motor_current": 1.2},
        "duration_ticks": 35,
        "auto_resolve": True,
    },
    ScenarioType.POWER_SURGE: {
        "name": "Power Surge Event",
        "description": "Electrical power surge affecting motor current and control systems",
        "default_machine": "M5",
        "fault_injections": {"motor_current": 2.0, "speed": 1.4, "temperature": 1.3},
        "duration_ticks": 10,
        "auto_resolve": True,
    },
}


class ActiveScenario:
    """Represents a running scenario instance."""

    def __init__(self, scenario_id: str, scenario_type: str,
                 machine_id: str, definition: Dict,
                 intensity: float, duration_ticks: int):
        self.scenario_id = scenario_id
        self.scenario_type = scenario_type
        self.machine_id = machine_id
        self.definition = definition
        self.intensity = intensity
        self.max_ticks = duration_ticks
        self.ticks_elapsed = 0
        self.is_active = True
        self.started_at = datetime.utcnow().isoformat()
        self.resolved_at: Optional[str] = None

    def tick(self) -> bool:
        """Advance scenario by one tick. Returns True if still active."""
        self.ticks_elapsed += 1
        if self.ticks_elapsed >= self.max_ticks and self.definition.get("auto_resolve"):
            self.is_active = False
            self.resolved_at = datetime.utcnow().isoformat()
            return False
        return self.is_active

    def to_dict(self) -> Dict:
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "name": self.definition.get("name", self.scenario_type),
            "description": self.definition.get("description", ""),
            "machine_id": self.machine_id,
            "intensity": self.intensity,
            "ticks_elapsed": self.ticks_elapsed,
            "max_ticks": self.max_ticks,
            "progress_pct": round(self.ticks_elapsed / max(1, self.max_ticks) * 100, 1),
            "is_active": self.is_active,
            "started_at": self.started_at,
            "resolved_at": self.resolved_at,
        }


class ScenarioEngine:
    """
    Manages scenario lifecycle: trigger, tick, and auto-resolve.
    Multiple scenarios can run simultaneously.
    """

    def __init__(self, simulation: "FactorySimulation"):
        self._simulation = simulation
        self._active_scenarios: Dict[str, ActiveScenario] = {}
        self._scenario_history: deque = deque(maxlen=50)
        self._tick: int = 0

    def trigger(self, scenario_type: str, machine_id: Optional[str] = None,
                intensity: float = 1.0, duration_seconds: int = 30) -> Dict[str, Any]:
        """Trigger a new scenario."""
        definition = SCENARIO_DEFINITIONS.get(scenario_type)
        if not definition:
            return {"success": False, "error": f"Unknown scenario type: {scenario_type}"}

        target_machine = machine_id or definition.get("default_machine", "M1")
        duration_ticks = max(5, int(duration_seconds / 2))  # 2s per tick

        scenario_id = f"SCN_{scenario_type[:6].upper()}_{uuid.uuid4().hex[:6].upper()}"
        active = ActiveScenario(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            machine_id=target_machine,
            definition=definition,
            intensity=intensity,
            duration_ticks=duration_ticks,
        )
        self._active_scenarios[scenario_id] = active

        # Inject faults into simulation
        fault_injections = definition.get("fault_injections", {})
        for sensor, multiplier in fault_injections.items():
            # Scale by intensity
            scaled_multiplier = 1.0 + (multiplier - 1.0) * intensity
            self._simulation.inject_fault(target_machine, sensor, scaled_multiplier)

        return {
            "success": True,
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "name": definition["name"],
            "machine_id": target_machine,
            "intensity": intensity,
            "duration_ticks": duration_ticks,
            "started_at": active.started_at,
        }

    def tick_all(self):
        """Advance all active scenarios by one tick. Called from main simulation loop."""
        self._tick += 1
        to_resolve = []

        for scenario_id, scenario in self._active_scenarios.items():
            still_active = scenario.tick()
            if not still_active:
                to_resolve.append(scenario_id)

        for scenario_id in to_resolve:
            scenario = self._active_scenarios.pop(scenario_id)
            self._scenario_history.append(scenario.to_dict())
            # Restore machine to normal
            self._simulation.reset_machine(scenario.machine_id)

    def stop(self, scenario_id: str) -> Dict[str, Any]:
        """Stop a specific scenario."""
        scenario = self._active_scenarios.pop(scenario_id, None)
        if not scenario:
            return {"success": False, "error": f"Scenario {scenario_id} not found"}
        scenario.is_active = False
        scenario.resolved_at = datetime.utcnow().isoformat()
        self._scenario_history.append(scenario.to_dict())
        self._simulation.reset_machine(scenario.machine_id)
        return {"success": True, "scenario_id": scenario_id, "status": "stopped"}

    def stop_all(self) -> Dict[str, Any]:
        """Stop all active scenarios and restore factory to normal."""
        count = len(self._active_scenarios)
        for scenario_id, scenario in list(self._active_scenarios.items()):
            scenario.is_active = False
            scenario.resolved_at = datetime.utcnow().isoformat()
            self._scenario_history.append(scenario.to_dict())
        self._active_scenarios.clear()
        self._simulation.reset_all_machines()
        return {"success": True, "stopped_count": count, "status": "all_stopped"}

    def get_active_scenarios(self) -> List[Dict[str, Any]]:
        """Return list of currently active scenario dicts."""
        return [s.to_dict() for s in self._active_scenarios.values()]

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Return all available scenario definitions."""
        return [
            {
                "type": stype,
                "name": defn["name"],
                "description": defn["description"],
                "default_machine": defn.get("default_machine"),
                "default_duration_ticks": defn.get("duration_ticks", 20),
            }
            for stype, defn in SCENARIO_DEFINITIONS.items()
        ]

    def get_history(self) -> List[Dict]:
        return list(self._scenario_history)
