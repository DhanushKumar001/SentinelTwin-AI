"""
SentinelTwin AI — Factory Simulation Engine
Simulates a 5-machine smart factory with realistic sensor data, state machines,
physics-based degradation, and full history tracking.
Tick interval: 2 seconds. All 5 machines operate in production sequence.
"""

import math
import random
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import (
    MACHINE_MAP,
    MACHINES,
    SIMULATION,
    THRESHOLDS,
    AlertLevel,
    MachineConfig,
    MachineStatus,
    PIPELINE_COLORS,
)


class MachineSensorState:
    """
    Holds the complete real-time sensor state of one factory machine.
    All sensor values evolve naturally each tick with noise and degradation.
    """

    def __init__(self, config: MachineConfig):
        self.config = config
        self.machine_id = config.machine_id
        self.name = config.name
        self.machine_type = config.machine_type

        # Current sensor values (start near nominal)
        self.temperature: float = config.nominal_temp + random.uniform(-2, 2)
        self.vibration: float = config.nominal_vibration + random.uniform(-0.2, 0.2)
        self.motor_current: float = config.nominal_current + random.uniform(-2, 2)
        self.speed: float = config.nominal_speed + random.uniform(-20, 20)
        self.load: float = config.nominal_load + random.uniform(-3, 3)
        self.production_rate: float = config.production_rate_nominal + random.uniform(-2, 2)
        self.runtime_hours: float = config.runtime_hours_initial

        # Machine state
        self.status: str = MachineStatus.NORMAL
        self.health_score: float = 100.0 - (config.runtime_hours_initial / 500.0)
        self.health_score = max(50.0, min(100.0, self.health_score))

        # Degradation and anomaly state
        self.degradation_level: float = 0.0
        self.is_overheating: bool = False
        self.has_vibration_fault: bool = False
        self.is_under_cyber_attack: bool = False
        self.current_fault_code: Optional[str] = None

        # Fault injection (set by scenario engine or self-healing)
        self._fault_multipliers: Dict[str, float] = {
            "temperature": 1.0,
            "vibration": 1.0,
            "motor_current": 1.0,
            "speed": 1.0,
            "load": 1.0,
        }
        self._healing_active: bool = False
        self._healing_target: Dict[str, float] = {}

        # Sensor history (ring buffer)
        self.history: deque = deque(maxlen=SIMULATION.history_length)
        self._tick_count: int = 0

    def tick(self) -> Dict[str, Any]:
        """
        Advance this machine's state by one simulation tick.
        Returns a snapshot of current sensor readings.
        """
        self._tick_count += 1
        self.runtime_hours += SIMULATION.tick_interval / 3600.0

        # Apply natural sensor noise and drift
        noise = SIMULATION.sensor_noise_factor
        self.temperature = self._drift(
            self.temperature,
            self.config.nominal_temp * self._fault_multipliers["temperature"],
            noise * 3, speed=0.05
        )
        self.vibration = self._drift(
            self.vibration,
            self.config.nominal_vibration * self._fault_multipliers["vibration"],
            noise * 0.5, speed=0.04
        )
        self.motor_current = self._drift(
            self.motor_current,
            self.config.nominal_current * self._fault_multipliers["motor_current"],
            noise * 2, speed=0.06
        )
        self.speed = self._drift(
            self.speed,
            self.config.nominal_speed * self._fault_multipliers["speed"],
            noise * 20, speed=0.03
        )
        self.load = self._drift(
            self.load,
            self.config.nominal_load * self._fault_multipliers["load"],
            noise * 2, speed=0.05
        )

        # Degradation slowly worsens sensor readings over time
        self.degradation_level = min(1.0, self.degradation_level + SIMULATION.degradation_rate)
        degradation_effect = self.degradation_level * 5.0
        self.temperature += degradation_effect * 0.3
        self.vibration += degradation_effect * 0.1

        # Production rate depends on machine health and load
        load_factor = max(0.5, 1.0 - (self.load - 100.0) / 200.0) if self.load > 100 else 1.0
        health_factor = self.health_score / 100.0
        self.production_rate = (
            self.config.production_rate_nominal * load_factor * health_factor
            + random.uniform(-1.5, 1.5)
        )
        self.production_rate = max(0.0, min(100.0, self.production_rate))

        # Apply healing if active
        if self._healing_active:
            self._apply_healing_step()

        # Recalculate health score
        self._recalculate_health()

        # Recalculate status
        self._recalculate_status()

        snapshot = self._snapshot()
        self.history.append(snapshot)
        return snapshot

    def _drift(self, current: float, target: float, noise_mag: float, speed: float) -> float:
        """Drift current value toward target with noise (mean-reverting random walk)."""
        noise = random.gauss(0, noise_mag)
        drift = (target - current) * speed
        return current + drift + noise

    def _recalculate_health(self) -> None:
        """Compute health score from sensor deviations and degradation."""
        temp_dev = max(0.0, (self.temperature - self.config.nominal_temp) / self.config.nominal_temp)
        vib_dev = max(0.0, (self.vibration - self.config.nominal_vibration) / max(1.0, self.config.nominal_vibration))
        curr_dev = max(0.0, (self.motor_current - self.config.nominal_current) / self.config.nominal_current)
        degrad = self.degradation_level

        penalty = (temp_dev * 20.0) + (vib_dev * 25.0) + (curr_dev * 15.0) + (degrad * 10.0)
        self.health_score = max(0.0, min(100.0, 100.0 - penalty))

    def _recalculate_status(self) -> None:
        """Map sensor readings to machine status enum."""
        if self._healing_active:
            self.status = MachineStatus.HEALING
            return

        t = self.temperature
        v = self.vibration
        c = self.motor_current

        if (t >= THRESHOLDS.temp_critical or
                v >= THRESHOLDS.vibration_critical or
                c >= THRESHOLDS.current_critical or
                self.health_score < 20.0):
            self.status = MachineStatus.FAILURE if self.health_score < 10.0 else MachineStatus.CRITICAL
        elif (t >= THRESHOLDS.temp_warning or
              v >= THRESHOLDS.vibration_warning or
              c >= THRESHOLDS.current_warning or
              self.health_score < 50.0):
            self.status = MachineStatus.WARNING
        else:
            self.status = MachineStatus.NORMAL

    def _apply_healing_step(self) -> None:
        """Gradually restore sensor readings toward nominal values during healing."""
        HEAL_RATE = 0.08
        all_healed = True
        for sensor, target in self._healing_target.items():
            current = getattr(self, sensor, None)
            if current is None:
                continue
            diff = target - current
            if abs(diff) > 0.5:
                setattr(self, sensor, current + diff * HEAL_RATE)
                all_healed = False
            else:
                setattr(self, sensor, target)

        if all_healed:
            self._healing_active = False
            self._healing_target = {}
            self._fault_multipliers = {k: 1.0 for k in self._fault_multipliers}
            self.degradation_level = max(0.0, self.degradation_level - 0.1)

    def set_fault(self, sensor: str, multiplier: float) -> None:
        """Inject a fault condition into a sensor (used by scenario engine)."""
        if sensor in self._fault_multipliers:
            self._fault_multipliers[sensor] = multiplier
            self._healing_active = False

    def start_healing(self, targets: Optional[Dict[str, float]] = None) -> None:
        """Begin self-healing, restoring sensors toward nominal."""
        self._healing_active = True
        self._healing_target = targets or {
            "temperature": self.config.nominal_temp,
            "vibration": self.config.nominal_vibration,
            "motor_current": self.config.nominal_current,
            "speed": self.config.nominal_speed,
            "load": self.config.nominal_load,
        }
        self._fault_multipliers = {k: 1.0 for k in self._fault_multipliers}

    def reset_to_normal(self) -> None:
        """Instantly reset machine to nominal operating state."""
        self.temperature = self.config.nominal_temp + random.uniform(-1, 1)
        self.vibration = self.config.nominal_vibration + random.uniform(-0.1, 0.1)
        self.motor_current = self.config.nominal_current + random.uniform(-1, 1)
        self.speed = self.config.nominal_speed + random.uniform(-10, 10)
        self.load = self.config.nominal_load + random.uniform(-2, 2)
        self.degradation_level = max(0.0, self.degradation_level - 0.2)
        self._fault_multipliers = {k: 1.0 for k in self._fault_multipliers}
        self._healing_active = False
        self._healing_target = {}
        self.is_overheating = False
        self.has_vibration_fault = False
        self.is_under_cyber_attack = False
        self.current_fault_code = None
        self._recalculate_health()
        self._recalculate_status()

    def _snapshot(self) -> Dict[str, Any]:
        """Return a snapshot dict of all current sensor readings."""
        return {
            "machine_id": self.machine_id,
            "name": self.name,
            "machine_type": self.machine_type,
            "timestamp": datetime.utcnow().isoformat(),
            "sensors": {
                "temperature": round(self.temperature, 2),
                "vibration": round(self.vibration, 3),
                "motor_current": round(self.motor_current, 2),
                "speed": round(self.speed, 1),
                "load": round(self.load, 2),
                "production_rate": round(self.production_rate, 2),
                "runtime_hours": round(self.runtime_hours, 1),
            },
            "status": self.status,
            "health_score": round(self.health_score, 1),
            "degradation_level": round(self.degradation_level, 4),
            "pipeline_color": PIPELINE_COLORS.get(self.status, "#2196F3"),
            "is_healing": self._healing_active,
            "fault_code": self.current_fault_code,
            "is_under_cyber_attack": self.is_under_cyber_attack,
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the last N sensor snapshots."""
        snapshots = list(self.history)
        return snapshots[-limit:]


class ConveyorBelt:
    """
    Simulates a conveyor belt segment connecting two machines.
    Products move along the belt based on upstream machine production rate.
    """

    def __init__(self, belt_id: str, from_machine: str, to_machine: str):
        self.belt_id = belt_id
        self.from_machine = from_machine
        self.to_machine = to_machine
        self.speed: float = 1.0          # m/s
        self.items_in_transit: int = 0
        self.is_running: bool = True
        self.belt_utilization: float = 0.0

    def tick(self, upstream_rate: float, downstream_rate: float) -> Dict[str, Any]:
        """Update conveyor state based on upstream and downstream production."""
        if not self.is_running:
            self.items_in_transit = max(0, self.items_in_transit - 1)
            self.belt_utilization = 0.0
        else:
            # Items accumulate if downstream is slower than upstream
            inflow = max(0, int(upstream_rate / 20))
            outflow = max(0, int(downstream_rate / 20))
            self.items_in_transit = max(0, min(20, self.items_in_transit + inflow - outflow))
            self.belt_utilization = min(1.0, self.items_in_transit / 20.0)
            self.speed = 0.8 + (downstream_rate / 200.0)

        return {
            "belt_id": self.belt_id,
            "from_machine": self.from_machine,
            "to_machine": self.to_machine,
            "speed": round(self.speed, 2),
            "items_in_transit": self.items_in_transit,
            "utilization": round(self.belt_utilization, 3),
            "is_running": self.is_running,
        }


class FactorySimulation:
    """
    Master factory simulation controlling all 5 machines, 4 conveyor belts,
    and the overall production line state. This is the heart of SentinelTwin.
    """

    def __init__(self):
        self._machines: Dict[str, MachineSensorState] = {
            m.machine_id: MachineSensorState(m) for m in MACHINES
        }
        self._conveyor_belts = [
            ConveyorBelt("CB1", "M1", "M2"),
            ConveyorBelt("CB2", "M2", "M3"),
            ConveyorBelt("CB3", "M3", "M4"),
            ConveyorBelt("CB4", "M4", "M5"),
        ]
        self._tick_count: int = 0
        self._start_time: datetime = datetime.utcnow()
        self._total_production: float = 0.0
        self._daily_production_target: float = 8640.0  # units/day at 100% eff
        self._bottleneck_machine: Optional[str] = None
        self._factory_status: str = "running"

        # Bottleneck detection history
        self._throughput_history: deque = deque(maxlen=30)

    def tick(self) -> Dict[str, Any]:
        """
        Advance the factory simulation by one tick.
        Returns the full factory state dict for broadcasting.
        """
        self._tick_count += 1

        # Tick all machines
        machine_states = {}
        for machine_id, machine in self._machines.items():
            machine_states[machine_id] = machine.tick()

        # Tick all conveyor belts
        conveyor_states = []
        machine_ids = ["M1", "M2", "M3", "M4", "M5"]
        for i, belt in enumerate(self._conveyor_belts):
            upstream_rate = machine_states[machine_ids[i]]["sensors"]["production_rate"]
            downstream_rate = machine_states[machine_ids[i + 1]]["sensors"]["production_rate"]
            conveyor_states.append(belt.tick(upstream_rate, downstream_rate))

        # Compute overall production throughput
        rates = [machine_states[mid]["sensors"]["production_rate"] for mid in machine_ids]
        # Throughput is limited by the slowest machine (bottleneck)
        throughput = min(rates)
        self._total_production += throughput * SIMULATION.tick_interval / 3600.0
        self._throughput_history.append(throughput)

        # Detect bottleneck
        min_rate = min(rates)
        bottleneck_idx = rates.index(min_rate)
        self._bottleneck_machine = machine_ids[bottleneck_idx] if min_rate < 80.0 else None

        # Factory-wide status
        statuses = [machine_states[mid]["status"] for mid in machine_ids]
        if MachineStatus.FAILURE in statuses:
            self._factory_status = "degraded"
        elif MachineStatus.CRITICAL in statuses:
            self._factory_status = "critical"
        elif MachineStatus.WARNING in statuses:
            self._factory_status = "warning"
        else:
            self._factory_status = "running"

        uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()

        return {
            "machines": machine_states,
            "conveyors": conveyor_states,
            "factory": {
                "status": self._factory_status,
                "tick": self._tick_count,
                "uptime_seconds": round(uptime_seconds, 0),
                "total_production_units": round(self._total_production, 1),
                "current_throughput": round(throughput, 2),
                "throughput_history": list(self._throughput_history),
                "bottleneck_machine": self._bottleneck_machine,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    def get_current_state(self) -> Dict[str, Any]:
        """Return the current state without advancing the simulation."""
        machine_states = {}
        for machine_id, machine in self._machines.items():
            machine_states[machine_id] = machine._snapshot()

        conveyor_states = []
        machine_ids = ["M1", "M2", "M3", "M4", "M5"]
        for i, belt in enumerate(self._conveyor_belts):
            upstream_rate = machine_states[machine_ids[i]]["sensors"]["production_rate"]
            downstream_rate = machine_states[machine_ids[i + 1]]["sensors"]["production_rate"]
            conveyor_states.append(belt.tick(upstream_rate, downstream_rate))

        return {
            "machines": machine_states,
            "conveyors": conveyor_states,
            "factory": {
                "status": self._factory_status,
                "tick": self._tick_count,
                "total_production_units": round(self._total_production, 1),
                "bottleneck_machine": self._bottleneck_machine,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    def get_machine_list(self) -> List[Dict[str, Any]]:
        """Return summary list of all machines."""
        result = []
        for machine_id, machine in self._machines.items():
            snap = machine._snapshot()
            result.append(snap)
        return result

    def get_machine_detail(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Return full detail for one machine."""
        machine = self._machines.get(machine_id)
        if not machine:
            return None
        snap = machine._snapshot()
        snap["history"] = machine.get_history(20)
        snap["nominal_values"] = {
            "temperature": machine.config.nominal_temp,
            "vibration": machine.config.nominal_vibration,
            "motor_current": machine.config.nominal_current,
            "speed": machine.config.nominal_speed,
            "load": machine.config.nominal_load,
        }
        return snap

    def get_machine_history(self, machine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return sensor history for one machine."""
        machine = self._machines.get(machine_id)
        if not machine:
            return []
        return machine.get_history(limit)

    def get_machine_state(self, machine_id: str) -> Optional[MachineSensorState]:
        """Return the raw machine state object (for use by AI modules)."""
        return self._machines.get(machine_id)

    def get_all_machine_states(self) -> Dict[str, MachineSensorState]:
        """Return all machine state objects."""
        return dict(self._machines)

    def apply_healing_action(self, action: Dict[str, Any]) -> None:
        """Apply a self-healing action to a machine."""
        machine_id = action.get("machine_id")
        action_type = action.get("action")
        machine = self._machines.get(machine_id)
        if not machine:
            return

        if action_type == "reduce_speed":
            machine.set_fault("speed", 0.7)
            machine.set_fault("load", 0.75)
        elif action_type == "activate_cooling":
            machine.set_fault("temperature", 0.7)
        elif action_type == "reduce_load":
            machine.set_fault("load", 0.6)
            machine.set_fault("motor_current", 0.8)
        elif action_type == "full_restore":
            machine.start_healing()
        elif action_type == "emergency_stop":
            machine.set_fault("speed", 0.0)
            machine.set_fault("load", 0.0)
            machine.status = MachineStatus.OFFLINE
        elif action_type == "restart":
            machine.reset_to_normal()

    def apply_command(self, machine_id: str, command: str, value: Optional[float] = None) -> Dict[str, Any]:
        """Apply an operator command to a machine."""
        machine = self._machines.get(machine_id)
        if not machine:
            return {"success": False, "error": f"Machine {machine_id} not found"}

        if command == "set_speed" and value is not None:
            ratio = value / machine.config.nominal_speed
            machine.set_fault("speed", ratio)
            return {"success": True, "machine_id": machine_id, "command": command, "value": value}
        elif command == "set_load" and value is not None:
            ratio = value / machine.config.nominal_load
            machine.set_fault("load", ratio)
            return {"success": True, "machine_id": machine_id, "command": command, "value": value}
        elif command == "emergency_stop":
            machine.status = MachineStatus.OFFLINE
            machine.set_fault("speed", 0.0)
            return {"success": True, "machine_id": machine_id, "command": "emergency_stop"}
        elif command == "reset":
            machine.reset_to_normal()
            return {"success": True, "machine_id": machine_id, "command": "reset"}
        else:
            return {"success": False, "error": f"Unknown command: {command}"}

    def reset_machine(self, machine_id: str) -> Dict[str, Any]:
        """Reset a single machine to normal state."""
        machine = self._machines.get(machine_id)
        if not machine:
            return {"success": False, "error": f"Machine {machine_id} not found"}
        machine.reset_to_normal()
        return {"success": True, "machine_id": machine_id, "status": "reset_to_normal"}

    def reset_all_machines(self) -> None:
        """Reset all machines to normal operating state."""
        for machine in self._machines.values():
            machine.reset_to_normal()
        self._factory_status = "running"
        self._bottleneck_machine = None

    def get_production_stats(self) -> Dict[str, Any]:
        """Return production throughput statistics."""
        history = list(self._throughput_history)
        avg_throughput = sum(history) / len(history) if history else 0.0
        return {
            "total_production_units": round(self._total_production, 1),
            "current_throughput": round(history[-1] if history else 0.0, 2),
            "average_throughput": round(avg_throughput, 2),
            "throughput_history": history,
            "bottleneck_machine": self._bottleneck_machine,
            "daily_target": self._daily_production_target,
            "efficiency_vs_target": round(avg_throughput / 100.0 * 100, 1),
        }

    def inject_fault(self, machine_id: str, sensor: str, multiplier: float) -> bool:
        """
        Inject a fault condition into a machine sensor.
        Used by scenario engine to simulate failures.
        """
        machine = self._machines.get(machine_id)
        if machine:
            machine.set_fault(sensor, multiplier)
            return True
        return False

    def get_sensor_values_array(self) -> Dict[str, Dict[str, float]]:
        """
        Return a flat dict of {machine_id: {sensor: value}} for AI modules.
        Optimized format for model inference.
        """
        result = {}
        for machine_id, machine in self._machines.items():
            result[machine_id] = {
                "temperature": machine.temperature,
                "vibration": machine.vibration,
                "motor_current": machine.motor_current,
                "speed": machine.speed,
                "load": machine.load,
                "production_rate": machine.production_rate,
                "health_score": machine.health_score,
                "degradation_level": machine.degradation_level,
            }
        return result
