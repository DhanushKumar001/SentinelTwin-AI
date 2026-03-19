"""
SentinelTwin AI — Predictive Maintenance Module
Simulates TCN, LSTM, and Temporal Fusion Transformer models for failure prediction.
Computes failure probability, remaining useful life (RUL), and maintenance recommendations.
"""

import math
import random
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from sentinelcore.config import MACHINES, MACHINE_MAP, THRESHOLDS, MachineStatus, MachineConfig


class TCNPredictor:
    """
    Temporal Convolutional Network predictor simulation.
    Analyzes recent sensor window using convolution-inspired feature extraction.
    """

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        # Simulated learned kernel weights (what sensors TCN finds most predictive)
        self.temp_weight = 0.35
        self.vibration_weight = 0.40
        self.current_weight = 0.25

    def predict(self, sensor_window: List[Dict[str, float]]) -> float:
        """
        Predict failure probability from a sliding window of sensor readings.
        Returns a probability in [0, 1].
        """
        if len(sensor_window) < 3:
            return 0.0

        # Extract feature trends (simulated TCN receptive field analysis)
        temps = [s.get("temperature", 0) for s in sensor_window]
        vibs = [s.get("vibration", 0) for s in sensor_window]
        currents = [s.get("motor_current", 0) for s in sensor_window]

        # Trend: is the value accelerating upward?
        def trend_score(values: List[float], nominal: float, warning: float) -> float:
            if len(values) < 2:
                return 0.0
            recent = values[-5:] if len(values) >= 5 else values
            avg_recent = sum(recent) / len(recent)
            normalized = (avg_recent - nominal) / max(1.0, warning - nominal)
            # Detect acceleration (second derivative proxy)
            if len(values) >= 6:
                early = values[-6:-3]
                late = values[-3:]
                accel = (sum(late)/len(late)) - (sum(early)/len(early))
                normalized += max(0, accel / nominal * 3)
            return max(0.0, min(1.0, normalized))

        temp_score = trend_score(temps, 65.0, THRESHOLDS.temp_warning)
        vib_score = trend_score(vibs, 3.0, THRESHOLDS.vibration_warning)
        curr_score = trend_score(currents, 65.0, THRESHOLDS.current_warning)

        combined = (
            self.temp_weight * temp_score
            + self.vibration_weight * vib_score
            + self.current_weight * curr_score
        )
        return max(0.0, min(1.0, combined))


class LSTMPredictor:
    """
    Long Short-Term Memory predictor simulation.
    Maintains hidden state to capture long-range temporal dependencies.
    """

    def __init__(self):
        self._hidden_state: Dict[str, float] = defaultdict(float)
        self._cell_state: Dict[str, float] = defaultdict(float)
        # Simulated LSTM gate weights
        self._forget_bias = 0.7
        self._input_bias = 0.3
        self._output_bias = 0.6

    def predict(self, machine_id: str, current_sensors: Dict[str, float],
                historical_anomaly_count: int) -> float:
        """
        Predict failure probability using stateful temporal modeling.
        """
        # Forget gate: how much of previous state to retain
        forget = self._forget_bias * (1.0 - current_sensors.get("health_score", 100.0) / 100.0)

        # Input gate: contribution of current reading
        temp_norm = max(0, (current_sensors.get("temperature", 0) - 60.0) / 40.0)
        vib_norm = max(0, (current_sensors.get("vibration", 0) - 2.5) / 8.0)
        curr_norm = max(0, (current_sensors.get("motor_current", 0) - 55.0) / 45.0)
        deg_norm = current_sensors.get("degradation_level", 0)
        anomaly_factor = min(1.0, historical_anomaly_count / 10.0)

        input_val = (temp_norm * 0.3 + vib_norm * 0.35 + curr_norm * 0.2 + deg_norm * 0.1 + anomaly_factor * 0.05)

        # Update cell state
        prev_cell = self._cell_state[machine_id]
        new_cell = prev_cell * forget + input_val * self._input_bias
        new_cell = max(0.0, min(1.0, new_cell))
        self._cell_state[machine_id] = new_cell

        # Output gate
        output = math.tanh(new_cell) * self._output_bias
        self._hidden_state[machine_id] = output

        return max(0.0, min(1.0, output))

    def reset(self, machine_id: str) -> None:
        """Reset LSTM state for a machine (after healing/reset)."""
        self._hidden_state[machine_id] = 0.0
        self._cell_state[machine_id] = 0.0


class TFTPredictor:
    """
    Temporal Fusion Transformer predictor simulation.
    Uses variable selection, gating, and multi-horizon attention simulation.
    """

    def __init__(self):
        # Variable importance weights (simulating learned feature selection)
        self._variable_weights = {
            "temperature": 0.28,
            "vibration": 0.32,
            "motor_current": 0.20,
            "degradation_level": 0.12,
            "load": 0.08,
        }

    def predict(self, sensors: Dict[str, float], runtime_hours: float,
                nominal_temp: float, nominal_vib: float) -> Tuple[float, float, float]:
        """
        Predict failure probability with uncertainty bounds (10th, 50th, 90th percentiles).
        Returns (p10, median, p90) failure probabilities.
        """
        scores = {}

        # Normalize each sensor relative to its nominal and critical threshold
        temp = sensors.get("temperature", nominal_temp)
        vib = sensors.get("vibration", nominal_vib)
        curr = sensors.get("motor_current", 65.0)
        degrad = sensors.get("degradation_level", 0.0)
        load = sensors.get("load", 70.0)

        scores["temperature"] = max(0.0, (temp - nominal_temp * 0.9) / (THRESHOLDS.temp_critical - nominal_temp * 0.9))
        scores["vibration"] = max(0.0, (vib - nominal_vib * 0.8) / (THRESHOLDS.vibration_critical - nominal_vib * 0.8))
        scores["motor_current"] = max(0.0, (curr - 50.0) / (THRESHOLDS.current_critical - 50.0))
        scores["degradation_level"] = degrad
        scores["load"] = max(0.0, (load - 60.0) / 40.0)

        # Runtime age factor (machines near end-of-life have higher base probability)
        age_factor = min(0.3, runtime_hours / 50000.0)

        # Weighted combination (simulating TFT variable selection network)
        weighted = sum(
            self._variable_weights[k] * max(0.0, min(1.0, v))
            for k, v in scores.items()
        )
        median = max(0.0, min(1.0, weighted + age_factor))

        # Uncertainty bounds (simulating quantile regression heads)
        uncertainty = 0.05 + median * 0.1
        p10 = max(0.0, median - uncertainty * 1.5)
        p90 = min(1.0, median + uncertainty * 1.5)

        return p10, median, p90


class PredictiveMaintenance:
    """
    Ensemble predictive maintenance engine combining TCN, LSTM, and TFT predictions.
    Computes failure probability, RUL, and maintenance recommendations for all machines.
    """

    def __init__(self):
        self._tcn = TCNPredictor(window_size=20)
        self._lstm = LSTMPredictor()
        self._tft = TFTPredictor()

        # Sensor history per machine for TCN windowed analysis
        self._sensor_history: Dict[str, deque] = {
            m.machine_id: deque(maxlen=50) for m in MACHINES
        }
        # Anomaly count history per machine (fed to LSTM)
        self._anomaly_counts: Dict[str, int] = {m.machine_id: 0 for m in MACHINES}

        # Prediction history for trend analysis
        self._prediction_history: Dict[str, deque] = {
            m.machine_id: deque(maxlen=30) for m in MACHINES
        }

        # RUL estimates per machine (hours remaining)
        self._rul_estimates: Dict[str, float] = {}

    def predict(self, factory_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run predictive maintenance inference across all 5 machines.
        Returns a list of prediction results.
        """
        results = []
        machines = factory_state.get("machines", {})

        for machine_id, machine_data in machines.items():
            config = MACHINE_MAP.get(machine_id)
            if not config:
                continue

            sensors = machine_data.get("sensors", {})
            status = machine_data.get("status", MachineStatus.NORMAL)

            # Update sensor history
            self._sensor_history[machine_id].append(sensors)
            history = list(self._sensor_history[machine_id])

            # Run TCN prediction
            tcn_prob = self._tcn.predict(history)

            # Run LSTM prediction
            lstm_sensors = {**sensors, "degradation_level": machine_data.get("degradation_level", 0)}
            lstm_prob = self._lstm.predict(
                machine_id, lstm_sensors, self._anomaly_counts[machine_id]
            )

            # Run TFT prediction
            tft_p10, tft_median, tft_p90 = self._tft.predict(
                lstm_sensors,
                sensors.get("runtime_hours", config.runtime_hours_initial),
                config.nominal_temp,
                config.nominal_vibration,
            )

            # Ensemble: weighted average (TFT gets highest weight as most sophisticated)
            ensemble_prob = (
                0.25 * tcn_prob
                + 0.30 * lstm_prob
                + 0.45 * tft_median
            )

            # Add status-based floor
            if status == MachineStatus.CRITICAL:
                ensemble_prob = max(ensemble_prob, 0.75)
            elif status == MachineStatus.FAILURE:
                ensemble_prob = max(ensemble_prob, 0.92)
            elif status == MachineStatus.WARNING:
                ensemble_prob = max(ensemble_prob, 0.35)

            ensemble_prob = max(0.0, min(1.0, ensemble_prob))

            # Compute Remaining Useful Life (RUL)
            rul_hours = self._estimate_rul(machine_id, ensemble_prob, sensors, config)

            # Generate maintenance recommendation
            recommendation = self._generate_recommendation(ensemble_prob, rul_hours, status, config)

            # Alert level
            if ensemble_prob >= 0.85:
                alert_level = "critical"
            elif ensemble_prob >= 0.65:
                alert_level = "high"
            elif ensemble_prob >= 0.40:
                alert_level = "medium"
            else:
                alert_level = "low"

            pred_result = {
                "machine_id": machine_id,
                "machine_name": config.name,
                "failure_probability": round(ensemble_prob, 4),
                "failure_probability_pct": round(ensemble_prob * 100, 1),
                "rul_hours": round(rul_hours, 1),
                "rul_days": round(rul_hours / 24, 2),
                "alert_level": alert_level,
                "recommendation": recommendation,
                "model_predictions": {
                    "tcn": round(tcn_prob, 4),
                    "lstm": round(lstm_prob, 4),
                    "tft_p10": round(tft_p10, 4),
                    "tft_median": round(tft_median, 4),
                    "tft_p90": round(tft_p90, 4),
                },
                "contributing_sensors": self._get_contributing_sensors(sensors, config),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self._prediction_history[machine_id].append(ensemble_prob)
            results.append(pred_result)

        return results

    def _estimate_rul(self, machine_id: str, failure_prob: float,
                      sensors: Dict[str, float], config: MachineConfig) -> float:
        """
        Estimate Remaining Useful Life in hours.
        Uses failure probability trajectory and sensor degradation rate.
        """
        if failure_prob >= 0.95:
            return random.uniform(0.5, 4.0)
        elif failure_prob >= 0.80:
            return random.uniform(4.0, 24.0)

        # Base RUL from probability: linear interpolation between 0 (prob=1) and max_rul (prob=0)
        max_rul_hours = 2000.0  # 83 days at 100% health
        base_rul = max_rul_hours * (1.0 - failure_prob) ** 1.5

        # Adjust for runtime hours (older machines have less RUL remaining)
        runtime = sensors.get("runtime_hours", config.runtime_hours_initial)
        max_runtime = 25000.0  # assumed machine lifespan
        age_factor = max(0.1, 1.0 - runtime / max_runtime)
        rul = base_rul * age_factor

        # Cache for trend analysis
        self._rul_estimates[machine_id] = rul
        return max(0.5, rul)

    def _generate_recommendation(self, prob: float, rul_hours: float,
                                  status: str, config: MachineConfig) -> str:
        """Generate a human-readable maintenance recommendation."""
        if prob >= 0.90 or rul_hours < 4:
            return f"IMMEDIATE: Schedule emergency maintenance for {config.name}. Failure imminent."
        elif prob >= 0.75 or rul_hours < 24:
            return f"URGENT: Inspect {config.name} bearings and motor within 24 hours."
        elif prob >= 0.55 or rul_hours < 120:
            return f"SCHEDULED: Plan maintenance for {config.name} within 5 days. Monitor vibration closely."
        elif prob >= 0.35:
            return f"ADVISORY: Increased wear detected on {config.name}. Review at next scheduled maintenance."
        else:
            return f"NORMAL: {config.name} operating within acceptable parameters. Continue standard maintenance."

    def _get_contributing_sensors(self, sensors: Dict[str, float],
                                   config: MachineConfig) -> List[Dict[str, Any]]:
        """
        Compute SHAP-style feature contributions for the prediction.
        Returns top contributing sensor factors.
        """
        contributions = []

        temp_contrib = max(0.0, (sensors.get("temperature", 0) - config.nominal_temp) / config.nominal_temp)
        vib_contrib = max(0.0, (sensors.get("vibration", 0) - config.nominal_vibration) / max(1.0, config.nominal_vibration))
        curr_contrib = max(0.0, (sensors.get("motor_current", 0) - config.nominal_current) / config.nominal_current)
        degrad_contrib = sensors.get("degradation_level", 0) * 2.0

        raw_contribs = [
            ("Vibration spike", vib_contrib, "vibration"),
            ("Motor current increase", curr_contrib, "motor_current"),
            ("Temperature rise", temp_contrib, "temperature"),
            ("Component degradation", degrad_contrib, "degradation"),
        ]

        total = sum(c[1] for c in raw_contribs) or 1.0
        for name, value, sensor in raw_contribs:
            if value > 0.01:
                contributions.append({
                    "factor": name,
                    "sensor": sensor,
                    "contribution_pct": round(value / total * 100, 1),
                    "absolute_value": round(value, 4),
                    "current_reading": round(sensors.get(sensor, 0), 2) if sensor != "degradation" else round(sensors.get("degradation_level", 0), 4),
                })

        contributions.sort(key=lambda x: x["contribution_pct"], reverse=True)
        return contributions[:4]

    def increment_anomaly_count(self, machine_id: str) -> None:
        """Increment anomaly count for LSTM context (called by anomaly detector)."""
        self._anomaly_counts[machine_id] = self._anomaly_counts.get(machine_id, 0) + 1

    def reset_machine_state(self, machine_id: str) -> None:
        """Reset prediction state for a machine after repair."""
        self._lstm.reset(machine_id)
        self._anomaly_counts[machine_id] = 0
        if machine_id in self._prediction_history:
            self._prediction_history[machine_id].clear()

    def get_latest_predictions(self) -> Dict[str, float]:
        """Return latest failure probability per machine."""
        result = {}
        for machine_id, history in self._prediction_history.items():
            if history:
                result[machine_id] = list(history)[-1]
            else:
                result[machine_id] = 0.0
        return result
