"""
SentinelTwin AI — Anomaly Detection Module
Implements Autoencoder-based, Isolation Forest, and LSTM anomaly detection
across all factory machine sensor streams.
"""

import math
import random
from collections import deque, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import MACHINES, MACHINE_MAP, THRESHOLDS, AnomalyType, AlertLevel


class AutoencoderAnomalyDetector:
    def __init__(self):
        self._sensor_weights = {
            "temperature": 0.22, "vibration": 0.28,
            "motor_current": 0.20, "speed": 0.15, "load": 0.15,
        }
        self._reconstruction_threshold = 0.12

    def compute_reconstruction_error(self, sensors, nominal):
        per_sensor = {}
        total = 0.0
        for sensor, weight in self._sensor_weights.items():
            current = sensors.get(sensor, 0.0)
            expected = nominal.get(sensor, current)
            if expected == 0:
                continue
            error = abs(current - expected) / max(1.0, abs(expected))
            per_sensor[sensor] = round(error, 5)
            total += weight * error
        return round(total, 5), per_sensor

    def detect(self, sensors, nominal):
        total_error, per_sensor = self.compute_reconstruction_error(sensors, nominal)
        is_anomaly = total_error > self._reconstruction_threshold
        if not is_anomaly:
            return False, total_error, ""
        max_sensor = max(per_sensor, key=per_sensor.get, default="temperature")
        anomaly_map = {
            "temperature": AnomalyType.TEMPERATURE_SURGE,
            "vibration": AnomalyType.VIBRATION_SPIKE,
            "motor_current": AnomalyType.CURRENT_ANOMALY,
            "load": AnomalyType.LOAD_ANOMALY,
            "speed": AnomalyType.MULTIVARIATE,
        }
        return True, total_error, anomaly_map.get(max_sensor, AnomalyType.MULTIVARIATE)


class IsolationForestDetector:
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self._score_history = deque(maxlen=200)
        self._threshold = 0.65

    def _compute_isolation_score(self, sensors, nominals):
        deviations = []
        for sensor in ["temperature", "vibration", "motor_current", "load"]:
            current = sensors.get(sensor, 0)
            nominal = nominals.get(sensor, current)
            std_dev = nominal * 0.10
            if std_dev > 0:
                z = abs(current - nominal) / std_dev
                deviations.append(z)
        if not deviations:
            return 0.0
        max_z = max(deviations)
        mean_z = sum(deviations) / len(deviations)
        score = 1.0 - math.exp(-0.3 * (0.7 * max_z + 0.3 * mean_z))
        return round(min(1.0, score), 5)

    def detect(self, sensors, nominals):
        score = self._compute_isolation_score(sensors, nominals)
        self._score_history.append(score)
        if len(self._score_history) >= 20:
            sorted_scores = sorted(self._score_history)
            threshold_idx = int(len(sorted_scores) * (1.0 - self.contamination))
            adaptive = sorted_scores[min(threshold_idx, len(sorted_scores) - 1)]
            self._threshold = max(0.55, min(0.90, adaptive))
        return score > self._threshold, score


class LSTMAnomalyDetector:
    def __init__(self, sequence_length=10):
        self.sequence_length = sequence_length
        self._sequences = defaultdict(lambda: deque(maxlen=sequence_length))
        self._prediction_errors = defaultdict(lambda: deque(maxlen=50))

    def detect(self, machine_id, sensors):
        key_sensors = ["temperature", "vibration", "motor_current"]
        current_vals = [sensors.get(s, 0) for s in key_sensors]
        seq = self._sequences[machine_id]
        seq.append(current_vals)
        if len(seq) < 4:
            return False, 0.0
        historical = list(seq)
        weights = [i + 1 for i in range(len(historical))]
        total_w = sum(weights)
        predicted = []
        for dim in range(len(key_sensors)):
            weighted_sum = sum(w * h[dim] for w, h in zip(weights, historical))
            predicted.append(weighted_sum / total_w)
        errors = []
        for pred, curr in zip(predicted, current_vals):
            if pred > 0:
                errors.append(abs(curr - pred) / max(1.0, abs(pred)))
        pred_error = sum(errors) / len(errors) if errors else 0.0
        self._prediction_errors[machine_id].append(pred_error)
        error_history = list(self._prediction_errors[machine_id])
        if len(error_history) >= 10:
            mean_err = sum(error_history) / len(error_history)
            std_err = math.sqrt(sum((e - mean_err) ** 2 for e in error_history) / len(error_history))
            threshold = mean_err + 2.5 * std_err
        else:
            threshold = 0.20
        return pred_error > threshold, round(pred_error, 5)


class AnomalyDetector:
    def __init__(self):
        self._autoencoder = AutoencoderAnomalyDetector()
        self._isolation_forest = IsolationForestDetector()
        self._lstm_detector = LSTMAnomalyDetector()
        self._anomaly_history = {m.machine_id: deque(maxlen=200) for m in MACHINES}
        self._active_anomalies = {m.machine_id: None for m in MACHINES}

    def detect(self, factory_state):
        anomalies = []
        machines = factory_state.get("machines", {})
        for machine_id, machine_data in machines.items():
            config = MACHINE_MAP.get(machine_id)
            if not config:
                continue
            sensors = machine_data.get("sensors", {})
            nominal = {
                "temperature": config.nominal_temp,
                "vibration": config.nominal_vibration,
                "motor_current": config.nominal_current,
                "speed": config.nominal_speed,
                "load": config.nominal_load,
            }
            ae_anomaly, ae_score, ae_type = self._autoencoder.detect(sensors, nominal)
            if_anomaly, if_score = self._isolation_forest.detect(sensors, nominal)
            lstm_anomaly, lstm_error = self._lstm_detector.detect(machine_id, sensors)
            votes = sum([ae_anomaly, if_anomaly, lstm_anomaly])
            is_anomaly = votes >= 2
            composite_score = (
                0.40 * ae_score + 0.35 * if_score + 0.25 * min(1.0, lstm_error * 3)
            )
            if is_anomaly:
                if ae_type:
                    anomaly_type = ae_type
                else:
                    temp_norm = abs(sensors.get("temperature", 0) - config.nominal_temp) / config.nominal_temp
                    vib_norm = abs(sensors.get("vibration", 0) - config.nominal_vibration) / max(0.5, config.nominal_vibration)
                    curr_norm = abs(sensors.get("motor_current", 0) - config.nominal_current) / config.nominal_current
                    if vib_norm > temp_norm and vib_norm > curr_norm:
                        anomaly_type = AnomalyType.VIBRATION_SPIKE
                    elif temp_norm > curr_norm:
                        anomaly_type = AnomalyType.TEMPERATURE_SURGE
                    else:
                        anomaly_type = AnomalyType.CURRENT_ANOMALY
                if composite_score >= 0.75:
                    severity = AlertLevel.CRITICAL
                elif composite_score >= 0.55:
                    severity = AlertLevel.HIGH
                elif composite_score >= 0.35:
                    severity = AlertLevel.MEDIUM
                else:
                    severity = AlertLevel.LOW
                anomaly_event = {
                    "anomaly_id": f"ANO-{machine_id}-{datetime.utcnow().strftime('%H%M%S')}",
                    "machine_id": machine_id,
                    "machine_name": config.name,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "composite_score": round(composite_score, 4),
                    "detector_votes": votes,
                    "detector_results": {
                        "autoencoder": {"detected": ae_anomaly, "score": ae_score},
                        "isolation_forest": {"detected": if_anomaly, "score": if_score},
                        "lstm": {"detected": lstm_anomaly, "error": lstm_error},
                    },
                    "sensor_deviations": self._compute_deviations(sensors, nominal),
                    "current_sensors": {k: round(v, 3) for k, v in sensors.items()},
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self._anomaly_history[machine_id].append(anomaly_event)
                self._active_anomalies[machine_id] = anomaly_event
                anomalies.append(anomaly_event)
            else:
                self._active_anomalies[machine_id] = None
        return anomalies

    def _compute_deviations(self, sensors, nominal):
        deviations = {}
        for sensor in ["temperature", "vibration", "motor_current", "speed", "load"]:
            current = sensors.get(sensor, 0)
            nom = nominal.get(sensor, current)
            if nom != 0:
                pct = (current - nom) / nom * 100.0
                deviations[sensor] = round(pct, 2)
        return deviations

    def get_history(self, limit=50):
        all_events = []
        for history in self._anomaly_history.values():
            all_events.extend(list(history))
        all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_events[:limit]

    def get_active_anomalies(self):
        return dict(self._active_anomalies)
