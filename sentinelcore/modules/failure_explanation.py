"""
SentinelTwin AI — Failure Explanation Engine
Provides transparent, SHAP-style explanations for predictive maintenance decisions.
Implements feature importance ranking and causal contribution analysis.
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import MACHINE_MAP, THRESHOLDS


class FailureExplanationEngine:
    """
    Explainable AI engine that produces human-readable explanations
    for why the predictive maintenance model flagged a machine.

    Uses SHAP value simulation, feature importance ranking, and
    causal chain analysis to explain predictions.
    """

    def __init__(self):
        # Feature baseline values (global dataset averages, simulated)
        self._feature_baselines = {
            "temperature": 58.0,
            "vibration": 3.2,
            "motor_current": 62.0,
            "speed": 1300.0,
            "load": 68.0,
            "degradation_level": 0.05,
            "runtime_hours": 10000.0,
        }

        # Causal chain templates for common failure modes
        self._causal_templates = {
            "bearing_wear": [
                "Increased vibration amplitude",
                "Elevated bearing temperature",
                "Abnormal motor current draw",
                "Reduced machine speed stability",
                "Bearing wear confirmed",
            ],
            "overheating": [
                "Temperature rising above nominal",
                "Cooling system insufficient",
                "Increased thermal stress on components",
                "Material fatigue acceleration",
                "Thermal failure risk elevated",
            ],
            "electrical_fault": [
                "Motor current irregularity detected",
                "Voltage fluctuation in drive circuit",
                "Winding insulation degradation",
                "Phase imbalance developing",
                "Electrical failure risk elevated",
            ],
            "mechanical_overload": [
                "Load exceeding rated capacity",
                "Increased vibration from mechanical stress",
                "Motor current spike pattern",
                "Component fatigue under stress",
                "Mechanical overload failure risk",
            ],
            "general_degradation": [
                "Multiple sensors showing above-nominal readings",
                "Degradation accumulating over time",
                "Maintenance interval overdue",
                "Component wear approaching service limit",
                "Predictive failure threshold reached",
            ],
        }

    def explain(self, prediction: Dict[str, Any],
                factory_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete explanation for a predictive maintenance alert.

        Args:
            prediction: Output from PredictiveMaintenance.predict()
            factory_state: Current factory state with all sensor readings

        Returns:
            Explanation dict with SHAP values, feature importance, causal chain
        """
        machine_id = prediction.get("machine_id")
        failure_prob = prediction.get("failure_probability", 0.0)
        config = MACHINE_MAP.get(machine_id)

        if not config:
            return {"error": f"Unknown machine: {machine_id}"}

        machine_data = factory_state.get("machines", {}).get(machine_id, {})
        sensors = machine_data.get("sensors", {})
        status = machine_data.get("status", "normal")

        # Compute SHAP values for each feature
        shap_values = self._compute_shap_values(sensors, config, failure_prob)

        # Rank features by importance
        feature_ranking = self._rank_features(shap_values)

        # Identify primary failure mode
        failure_mode = self._identify_failure_mode(sensors, config, shap_values)

        # Build causal chain
        causal_chain = self._build_causal_chain(failure_mode, sensors, config)

        # Generate natural language explanation
        narrative = self._generate_narrative(
            machine_id, config.name, failure_prob, feature_ranking, failure_mode
        )

        # Generate recommended actions
        recommended_actions = self._generate_actions(failure_prob, failure_mode, config)

        return {
            "machine_id": machine_id,
            "machine_name": config.name,
            "failure_probability": round(failure_prob * 100, 1),
            "failure_mode": failure_mode,
            "shap_values": shap_values,
            "feature_ranking": feature_ranking,
            "causal_chain": causal_chain,
            "narrative": narrative,
            "recommended_actions": recommended_actions,
            "confidence": round(0.70 + failure_prob * 0.25, 3),
            "explanation_method": "SHAP + Causal Analysis",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _compute_shap_values(self, sensors: Dict[str, float],
                              config, failure_prob: float) -> Dict[str, float]:
        """
        Compute SHAP (SHapley Additive exPlanations) values for each sensor feature.
        Simulates the marginal contribution of each feature to the prediction.
        SHAP values sum to (prediction - baseline_prediction).
        """
        baseline_pred = 0.05  # baseline failure probability with nominal conditions

        # Deviations from nominal (normalized)
        temp_dev = max(0, sensors.get("temperature", config.nominal_temp) - config.nominal_temp) / config.nominal_temp
        vib_dev = max(0, sensors.get("vibration", config.nominal_vibration) - config.nominal_vibration) / max(0.5, config.nominal_vibration)
        curr_dev = max(0, sensors.get("motor_current", config.nominal_current) - config.nominal_current) / config.nominal_current
        speed_dev = abs(sensors.get("speed", config.nominal_speed) - config.nominal_speed) / config.nominal_speed
        load_dev = max(0, sensors.get("load", config.nominal_load) - config.nominal_load) / config.nominal_load
        degrad = sensors.get("degradation_level", 0.0)
        runtime_excess = max(0, sensors.get("runtime_hours", 0) - 15000) / 10000.0

        # Raw contributions (simulated Shapley allocation)
        raw = {
            "temperature": temp_dev * 0.28,
            "vibration": vib_dev * 0.32,
            "motor_current": curr_dev * 0.20,
            "speed_deviation": speed_dev * 0.08,
            "overload": load_dev * 0.07,
            "component_degradation": degrad * 0.15,
            "runtime_age": runtime_excess * 0.05,
        }

        # Scale so they sum to (failure_prob - baseline_pred)
        raw_total = sum(raw.values()) or 1e-9
        scale = max(0.0, failure_prob - baseline_pred) / raw_total

        shap_values = {k: round(v * scale, 5) for k, v in raw.items()}
        shap_values["baseline"] = round(baseline_pred, 5)

        return shap_values

    def _rank_features(self, shap_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Rank features by absolute SHAP value (feature importance ranking).
        Returns sorted list from most to least impactful.
        """
        features = [
            (k, v) for k, v in shap_values.items() if k != "baseline" and v > 0.001
        ]
        features.sort(key=lambda x: x[1], reverse=True)

        total_shap = sum(v for _, v in features) or 1e-9

        ranking = []
        feature_labels = {
            "temperature": "Temperature rise",
            "vibration": "Vibration spike",
            "motor_current": "Motor current increase",
            "speed_deviation": "Speed instability",
            "overload": "Mechanical overload",
            "component_degradation": "Component degradation",
            "runtime_age": "Runtime age factor",
        }

        for feature_key, shap_val in features:
            ranking.append({
                "rank": len(ranking) + 1,
                "feature": feature_key,
                "label": feature_labels.get(feature_key, feature_key),
                "shap_value": shap_val,
                "contribution_pct": round(shap_val / total_shap * 100, 1),
                "direction": "increases_risk",
            })

        return ranking[:5]  # Top 5 contributors

    def _identify_failure_mode(self, sensors: Dict[str, float],
                                config, shap_values: Dict[str, float]) -> str:
        """
        Identify the most likely failure mode based on sensor patterns.
        """
        vib_elevated = sensors.get("vibration", 0) > config.nominal_vibration * 1.5
        temp_elevated = sensors.get("temperature", 0) > config.nominal_temp * 1.2
        curr_elevated = sensors.get("motor_current", 0) > config.nominal_current * 1.15
        load_elevated = sensors.get("load", 0) > 90.0

        if vib_elevated and temp_elevated:
            return "bearing_wear"
        elif temp_elevated and not vib_elevated:
            return "overheating"
        elif curr_elevated and not vib_elevated:
            return "electrical_fault"
        elif load_elevated:
            return "mechanical_overload"
        else:
            return "general_degradation"

    def _build_causal_chain(self, failure_mode: str,
                             sensors: Dict[str, float],
                             config) -> List[Dict[str, str]]:
        """
        Build a causal chain showing how sensor anomalies lead to failure.
        Returns ordered list of cause → effect nodes.
        """
        template = self._causal_templates.get(failure_mode, self._causal_templates["general_degradation"])

        chain = []
        for i, step in enumerate(template):
            chain.append({
                "step": i + 1,
                "description": step,
                "type": "root_cause" if i == 0 else ("intermediate" if i < len(template) - 1 else "consequence"),
            })

        return chain

    def _generate_narrative(self, machine_id: str, machine_name: str,
                             failure_prob: float, feature_ranking: List[Dict],
                             failure_mode: str) -> str:
        """
        Generate a human-readable narrative explanation of the prediction.
        """
        prob_pct = failure_prob * 100

        if not feature_ranking:
            return f"Machine {machine_name} shows elevated failure risk based on multi-sensor analysis."

        top_factor = feature_ranking[0]["label"] if feature_ranking else "sensor anomaly"
        second_factor = feature_ranking[1]["label"] if len(feature_ranking) > 1 else None

        mode_descriptions = {
            "bearing_wear": "bearing wear pattern",
            "overheating": "thermal overload condition",
            "electrical_fault": "electrical system anomaly",
            "mechanical_overload": "mechanical overload stress",
            "general_degradation": "multi-factor degradation pattern",
        }
        mode_desc = mode_descriptions.get(failure_mode, "anomalous behavior pattern")

        narrative = (
            f"The AI model detected a {mode_desc} on {machine_name} with {prob_pct:.0f}% failure probability. "
            f"The primary driver is {top_factor.lower()}"
        )

        if second_factor:
            narrative += f", compounded by {second_factor.lower()}"

        narrative += (
            f". The model analyzed the last 50 sensor readings using an ensemble of "
            f"TCN, LSTM, and Temporal Fusion Transformer models to reach this conclusion."
        )

        return narrative

    def _generate_actions(self, failure_prob: float, failure_mode: str,
                           config) -> List[str]:
        """Generate ordered list of recommended maintenance actions."""
        base_actions = {
            "bearing_wear": [
                "Inspect and lubricate bearings immediately",
                "Measure bearing clearance and replace if outside tolerance",
                "Check shaft alignment and coupling condition",
                "Review lubrication schedule and oil quality",
            ],
            "overheating": [
                "Check cooling system flow rate and coolant level",
                "Clean heat exchanger and ventilation filters",
                "Reduce machine load by 20% temporarily",
                "Inspect thermal sensors for calibration drift",
            ],
            "electrical_fault": [
                "Inspect motor winding resistance and insulation",
                "Check drive inverter output voltage balance",
                "Measure phase current balance across all phases",
                "Review motor control cabinet for loose connections",
            ],
            "mechanical_overload": [
                "Reduce production load to 75% of rated capacity",
                "Inspect mechanical coupling and gear train",
                "Check for material jams or obstructions",
                "Verify load cell calibration accuracy",
            ],
            "general_degradation": [
                "Schedule comprehensive preventive maintenance",
                "Perform full sensor calibration check",
                "Review maintenance history and last service date",
                "Order replacement parts for critical wear components",
            ],
        }

        actions = base_actions.get(failure_mode, base_actions["general_degradation"])

        if failure_prob >= 0.85:
            actions.insert(0, "⚠️ IMMEDIATE: Remove machine from production line")

        return actions
