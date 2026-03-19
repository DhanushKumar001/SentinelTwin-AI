"""
SentinelTwin AI — Self-Healing Autonomous Control System
Automatically corrects machine problems using RL-based control strategies.
Simulates PPO, SAC, and DQN reinforcement learning algorithms.
"""

import random
from collections import deque, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import MACHINE_MAP, THRESHOLDS, MachineStatus, AlertLevel


# Available healing actions and their descriptions
HEALING_ACTIONS = {
    "reduce_speed": "Reduce machine speed by 30% to lower mechanical stress",
    "reduce_load": "Reduce production load by 40% to decrease motor current",
    "activate_cooling": "Activate auxiliary cooling system to reduce temperature",
    "redistribute_tasks": "Redistribute production tasks to adjacent machines",
    "full_restore": "Apply gradual self-healing to restore all sensors to nominal",
    "emergency_stop": "Emergency stop to prevent catastrophic failure",
    "restart": "Controlled restart after full system check",
    "monitor_only": "Increase monitoring frequency, no corrective action yet",
}


class PPOController:
    """
    Simulates Proximal Policy Optimization controller.
    Conservative policy updates — good for safe industrial control.
    """

    def __init__(self):
        # Simulated policy network weights (action probabilities per state)
        self._clip_ratio = 0.2  # PPO clipping
        self._action_log: deque = deque(maxlen=50)

    def select_action(self, state_vector: List[float], machine_id: str) -> Tuple[str, float]:
        """
        Select healing action based on current state.
        Returns (action_name, policy_confidence).
        """
        temp_norm, vib_norm, curr_norm, health_norm, status_code = state_vector

        # Policy: map normalized state to action probability distribution
        if status_code >= 0.9:  # FAILURE
            if vib_norm > 0.8:
                return "emergency_stop", 0.92
            else:
                return "full_restore", 0.85
        elif status_code >= 0.7:  # CRITICAL
            if temp_norm > 0.8:
                return "activate_cooling", 0.88
            elif vib_norm > 0.7:
                return "reduce_speed", 0.84
            else:
                return "reduce_load", 0.79
        elif status_code >= 0.4:  # WARNING
            if temp_norm > 0.6:
                return "activate_cooling", 0.74
            elif vib_norm > 0.5:
                return "reduce_speed", 0.70
            else:
                return "monitor_only", 0.65
        else:
            return "monitor_only", 0.55

    def compute_reward(self, health_before: float, health_after: float) -> float:
        """Compute PPO reward signal for learning."""
        return (health_after - health_before) * 10.0 - 2.0  # Action cost penalty


class SACController:
    """
    Simulates Soft Actor-Critic controller.
    Entropy-maximizing policy — explores diverse healing strategies.
    """

    def __init__(self):
        self._temperature = 0.2  # Entropy temperature
        self._value_estimates: Dict[str, float] = defaultdict(float)

    def select_action(self, state_vector: List[float], machine_id: str) -> Tuple[str, float]:
        """
        Select action with entropy-augmented policy for exploration.
        """
        temp_norm, vib_norm, curr_norm, health_norm, status_code = state_vector

        # SAC adds entropy bonus to explore diverse actions
        if status_code >= 0.85:
            candidates = [("full_restore", 0.90), ("emergency_stop", 0.85)]
        elif temp_norm > 0.75:
            candidates = [("activate_cooling", 0.86), ("reduce_load", 0.78)]
        elif vib_norm > 0.65:
            candidates = [("reduce_speed", 0.82), ("reduce_load", 0.75)]
        elif curr_norm > 0.65:
            candidates = [("reduce_load", 0.80), ("reduce_speed", 0.72)]
        else:
            candidates = [("monitor_only", 0.60), ("full_restore", 0.55)]

        # Add entropy: occasionally explore non-greedy actions
        if random.random() < self._temperature:
            return random.choice(candidates)
        return candidates[0]


class DQNController:
    """
    Simulates Deep Q-Network controller.
    Discrete action space with Q-value lookup.
    """

    def __init__(self):
        # Simulated Q-table: state_bucket -> action -> Q-value
        self._q_values: Dict[str, Dict[str, float]] = {}
        self._epsilon = 0.1  # Exploration rate

    def select_action(self, state_vector: List[float], machine_id: str) -> Tuple[str, float]:
        """Select action with epsilon-greedy policy."""
        temp_norm, vib_norm, curr_norm, health_norm, status_code = state_vector
        state_key = f"{int(temp_norm*3)}_{int(vib_norm*3)}_{int(status_code*3)}"

        if random.random() < self._epsilon:
            # Exploration
            action = random.choice(list(HEALING_ACTIONS.keys()))
            return action, 0.50

        # Greedy: use Q-value mapping
        q_map = {
            "reduce_speed": vib_norm * 0.9 + curr_norm * 0.5,
            "reduce_load": curr_norm * 0.85 + vib_norm * 0.4,
            "activate_cooling": temp_norm * 0.95,
            "full_restore": (1.0 - health_norm) * 0.85,
            "emergency_stop": status_code * 0.95 if status_code > 0.85 else 0.0,
            "monitor_only": (1.0 - status_code) * 0.6,
        }

        best_action = max(q_map.items(), key=lambda x: x[1])
        confidence = min(0.95, max(0.50, best_action[1]))
        return best_action[0], confidence


class SelfHealingController:
    """
    Autonomous self-healing system that evaluates machine states and applies
    corrective actions using ensemble RL policy (PPO + SAC + DQN).
    """

    def __init__(self):
        self._ppo = PPOController()
        self._sac = SACController()
        self._dqn = DQNController()

        self._healing_history: deque = deque(maxlen=100)
        self._active_actions: Dict[str, Dict] = {}
        self._action_cooldown: Dict[str, int] = {}
        self._health_before_healing: Dict[str, float] = {}

    def evaluate_and_act(self, factory_state: Dict[str, Any],
                          anomalies: List[Dict[str, Any]],
                          predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate each machine and determine if self-healing action is needed.
        Returns list of actions taken.
        """
        actions_taken = []
        machines = factory_state.get("machines", {})

        # Index anomalies and predictions by machine_id
        anomaly_map = {a["machine_id"]: a for a in anomalies}
        prediction_map = {p["machine_id"]: p for p in predictions}

        for machine_id, machine_data in machines.items():
            config = MACHINE_MAP.get(machine_id)
            if not config:
                continue

            # Check cooldown
            if self._action_cooldown.get(machine_id, 0) > 0:
                self._action_cooldown[machine_id] -= 1
                continue

            status = machine_data.get("status", MachineStatus.NORMAL)
            health = machine_data.get("health_score", 100.0)
            sensors = machine_data.get("sensors", {})

            # Skip normal machines with low failure probability
            failure_prob = prediction_map.get(machine_id, {}).get("failure_probability", 0.0)
            anomaly_score = anomaly_map.get(machine_id, {}).get("anomaly_score", 0.0)

            should_heal = (
                status in (MachineStatus.CRITICAL, MachineStatus.FAILURE, MachineStatus.WARNING)
                or failure_prob > 0.65
                or anomaly_score > 0.70
            )

            if not should_heal:
                continue

            # Build normalized state vector for RL controllers
            state_vector = self._build_state_vector(sensors, config, status, health)

            # Get action recommendations from all three controllers
            ppo_action, ppo_conf = self._ppo.select_action(state_vector, machine_id)
            sac_action, sac_conf = self._sac.select_action(state_vector, machine_id)
            dqn_action, dqn_conf = self._dqn.select_action(state_vector, machine_id)

            # Ensemble vote: weighted by confidence
            vote_map: Dict[str, float] = {}
            for action, conf, weight in [
                (ppo_action, ppo_conf, 0.40),
                (sac_action, sac_conf, 0.35),
                (dqn_action, dqn_conf, 0.25),
            ]:
                vote_map[action] = vote_map.get(action, 0.0) + conf * weight

            best_action = max(vote_map.items(), key=lambda x: x[1])
            action_name = best_action[0]
            action_confidence = min(0.99, best_action[1])

            # Skip monitor_only if things are really bad
            if action_name == "monitor_only" and status in (MachineStatus.CRITICAL, MachineStatus.FAILURE):
                action_name = "full_restore"
                action_confidence = 0.80

            action_record = {
                "action_id": f"HEAL_{machine_id}_{datetime.utcnow().strftime('%H%M%S')}",
                "machine_id": machine_id,
                "machine_name": config.name,
                "action": action_name,
                "action_description": HEALING_ACTIONS.get(action_name, action_name),
                "confidence": round(action_confidence, 3),
                "triggered_by": {
                    "status": status,
                    "failure_probability": round(failure_prob, 3),
                    "anomaly_score": round(anomaly_score, 3),
                    "health_score": round(health, 1),
                },
                "rl_votes": {
                    "ppo": {"action": ppo_action, "confidence": round(ppo_conf, 3)},
                    "sac": {"action": sac_action, "confidence": round(sac_conf, 3)},
                    "dqn": {"action": dqn_action, "confidence": round(dqn_conf, 3)},
                },
                "health_before": round(health, 1),
                "expected_recovery_ticks": self._estimate_recovery_ticks(action_name),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self._healing_history.append(action_record)
            self._active_actions[machine_id] = action_record
            self._health_before_healing[machine_id] = health

            # Set cooldown to prevent action spam
            cooldown = 20 if action_name == "emergency_stop" else 15
            self._action_cooldown[machine_id] = cooldown

            actions_taken.append(action_record)

        return actions_taken

    def _build_state_vector(self, sensors: Dict[str, float], config,
                             status: str, health: float) -> List[float]:
        """Normalize machine state into [0,1] vector for RL input."""
        temp = sensors.get("temperature", config.nominal_temp)
        vib = sensors.get("vibration", config.nominal_vibration)
        curr = sensors.get("motor_current", config.nominal_current)

        temp_norm = min(1.0, max(0.0, (temp - config.nominal_temp) / (THRESHOLDS.temp_critical - config.nominal_temp)))
        vib_norm = min(1.0, max(0.0, (vib - config.nominal_vibration) / (THRESHOLDS.vibration_critical - config.nominal_vibration)))
        curr_norm = min(1.0, max(0.0, (curr - config.nominal_current) / (THRESHOLDS.current_critical - config.nominal_current)))
        health_norm = 1.0 - (health / 100.0)

        status_codes = {
            MachineStatus.NORMAL: 0.0,
            MachineStatus.WARNING: 0.4,
            MachineStatus.CRITICAL: 0.75,
            MachineStatus.FAILURE: 1.0,
            MachineStatus.HEALING: 0.3,
        }
        status_code = status_codes.get(status, 0.0)

        return [temp_norm, vib_norm, curr_norm, health_norm, status_code]

    def _estimate_recovery_ticks(self, action: str) -> int:
        estimates = {
            "reduce_speed": 15,
            "reduce_load": 12,
            "activate_cooling": 20,
            "redistribute_tasks": 10,
            "full_restore": 30,
            "emergency_stop": 5,
            "restart": 25,
            "monitor_only": 0,
        }
        return estimates.get(action, 15)

    def get_healing_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        history = list(self._healing_history)
        return history[-limit:]

    def get_active_actions(self) -> Dict[str, Dict]:
        return dict(self._active_actions)
