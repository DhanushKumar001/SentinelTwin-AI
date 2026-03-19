"""
SentinelTwin AI — Dashboard 2 Engine
Processes every simulation tick and builds the complete Dashboard 2 payload.

Field names mapped exactly to the given modules:
  anomaly_detection     → composite_score, detector_votes, detector_results,
                          sensor_deviations, anomaly_type, severity
  predictive_maintenance→ failure_probability, rul_hours, model_predictions,
                          contributing_sensors, alert_level, recommendation
  self_healing          → action, action_description, confidence,
                          triggered_by, rl_votes, health_before
  cybersecurity         → threats[].threat_type, severity, target_machine
  efficiency_score      → factory_efficiency_score, grade
  scenario_engine       → scenario_id, name, machine_id, intensity, max_ticks
"""

from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── Display constants ─────────────────────────────────────────────────────────
MACHINE_NAMES = {
    "M1": "Raw Material Processor",
    "M2": "Assembly Robot",
    "M3": "Quality Inspector",
    "M4": "CNC Machining Center",
    "M5": "Packaging Unit",
}

THRESHOLDS = {
    "temperature":   (75.0, 90.0),
    "vibration":     (7.0, 10.0),
    "motor_current": (80.0, 95.0),
    "load":          (80.0, 95.0),
}

LOG_META = {
    "INFO":     {"color": "#64B5F6", "icon": "ℹ"},
    "SENSOR":   {"color": "#4DD0E1", "icon": "📡"},
    "AI":       {"color": "#CE93D8", "icon": "🤖"},
    "DECISION": {"color": "#FFB74D", "icon": "⚡"},
    "CONTROL":  {"color": "#FF8A65", "icon": "⚙"},
    "TWIN":     {"color": "#81C784", "icon": "🌐"},
    "RESPONSE": {"color": "#A5D6A7", "icon": "✅"},
    "WARN":     {"color": "#FFF176", "icon": "⚠"},
    "CRITICAL": {"color": "#EF9A9A", "icon": "🔴"},
    "HEAL":     {"color": "#80CBC4", "icon": "♻"},
    "CYBER":    {"color": "#FF80AB", "icon": "🛡"},
    "SCENARIO": {"color": "#FFCC02", "icon": "🎭"},
    "OPTIM":    {"color": "#69F0AE", "icon": "📈"},
    "DEFECT":   {"color": "#FF7043", "icon": "🔍"},
    "RCA":      {"color": "#B39DDB", "icon": "🧬"},
}


def _slevel(val: float, sensor: str) -> str:
    w, c = THRESHOLDS.get(sensor, (1e9, 1e9))
    return "critical" if val >= c else "warning" if val >= w else "normal"


# ─── Terminal log ─────────────────────────────────────────────────────────────

class TerminalLog:
    def __init__(self, maxlen: int = 500):
        self._entries: deque = deque(maxlen=maxlen)
        self._seq = 0

    def append(self, level: str, message: str,
               machine_id: Optional[str] = None,
               phase: str = "INFO") -> Dict:
        self._seq += 1
        meta = LOG_META.get(level, LOG_META["INFO"])
        entry = {
            "seq":        self._seq,
            "ts":         datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "level":      level,
            "icon":       meta["icon"],
            "color":      meta["color"],
            "machine_id": machine_id or "FACTORY",
            "message":    message,
            "phase":      phase,
        }
        self._entries.append(entry)
        return entry

    def get_recent(self, n: int = 80) -> List[Dict]:
        return list(self._entries)[-n:]

    def get_since(self, seq: int) -> List[Dict]:
        return [e for e in self._entries if e["seq"] > seq]

    def clear(self):
        self._entries.clear()


# ─── AI regulation tracker ────────────────────────────────────────────────────

class AIRegulationTracker:
    def __init__(self):
        self._state: Dict[str, Dict] = {}
        self._history: Dict[str, deque] = {}

    def update(self, machine_id: str, snapshot: Dict) -> None:
        self._state[machine_id] = snapshot
        if machine_id not in self._history:
            self._history[machine_id] = deque(maxlen=60)
        self._history[machine_id].append(snapshot)

    def get_all(self) -> Dict[str, Dict]:
        return dict(self._state)


# ─── Physical response tracker ───────────────────────────────────────────────

class PhysicalResponseTracker:
    def __init__(self):
        self._records: Dict[str, Dict] = {}
        self._history: deque = deque(maxlen=50)

    def record_action(self, machine_id: str, action: str,
                      before: Dict, after: Dict,
                      cause: str, severity: str) -> Dict:
        record = {
            "machine_id":   machine_id,
            "machine_name": MACHINE_NAMES.get(machine_id, machine_id),
            "action":       action,
            "cause":        cause,
            "severity":     severity,
            "before":       before,
            "after":        after,
            "delta":        {k: round(after.get(k, 0) - before.get(k, 0), 3) for k in before},
            "timestamp":    datetime.utcnow().isoformat(),
            "improvement":  self._improvement(before, after),
        }
        self._records[machine_id] = record
        self._history.append(record)
        return record

    @staticmethod
    def _improvement(before: Dict, after: Dict) -> float:
        keys = ["temperature", "vibration", "motor_current"]
        deltas = [(before.get(k, 0) - after.get(k, 0)) / max(1, before.get(k, 1))
                  for k in keys if before.get(k, 0) > 0]
        if not deltas:
            return 0.0
        return round(max(0.0, min(100.0, sum(deltas) / len(deltas) * 100)), 1)

    def get_all_latest(self) -> Dict[str, Dict]:
        return dict(self._records)

    def get_history(self, n: int = 20) -> List[Dict]:
        return list(self._history)[-n:]


# ═════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD 2 ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class Dashboard2Engine:
    """
    Called from main.py every simulation tick.
    Produces the full d2_tick payload broadcast to /ws/d2.
    """

    def __init__(self):
        self.log              = TerminalLog(maxlen=500)
        self.ai_tracker       = AIRegulationTracker()
        self.response_tracker = PhysicalResponseTracker()

        # Sparkline history per machine per sensor (last 40 values)
        self._sensor_history: Dict[str, Dict[str, deque]] = {
            mid: {s: deque(maxlen=40)
                  for s in ["temperature", "vibration", "motor_current",
                             "speed", "load", "health_score"]}
            for mid in MACHINE_NAMES
        }

        self._prev_sensors:       Dict[str, Dict] = {}
        self._healing_active:     Dict[str, bool] = {}
        self._before_healing:     Dict[str, Dict] = {}
        self._last_statuses:      Dict[str, str]  = {}
        self._last_scenario_ids:  set = set()
        self._tick = 0

        self.log.append("INFO",
            "Dashboard 2 Engine initialised — all modules connected")

    # ── Main tick ─────────────────────────────────────────────────────────────

    def process_tick(
        self,
        factory_state:    Dict[str, Any],
        anomalies:        List[Dict],
        predictions:      List[Dict],
        healing_actions:  List[Dict],
        cyber_events:     Dict,
        active_scenarios: List[Dict],
    ) -> Dict[str, Any]:
        self._tick += 1
        machines = factory_state.get("machines", {})
        factory  = factory_state.get("factory", {})

        # 1. Detect new scenarios
        current_ids = {s["scenario_id"] for s in active_scenarios}
        for sid in (current_ids - self._last_scenario_ids):
            s = next((x for x in active_scenarios if x["scenario_id"] == sid), None)
            if s:
                self.log.append("SCENARIO",
                    f"Scenario triggered: [{s['name']}] on {s['machine_id']} "
                    f"· intensity {s['intensity']:.1f}x · ~{s['max_ticks']*2}s",
                    machine_id=s["machine_id"], phase="PHYSICAL")
                self.log.append("SENSOR",
                    f"Fault injection active → {s.get('description', '')}",
                    machine_id=s["machine_id"], phase="PHYSICAL")
        self._last_scenario_ids = current_ids

        # 2. Sensor panel
        sensor_panel = self._build_sensor_panel(machines)

        # 3. AI regulation panel (uses exact fields from anomaly_detection + predictive_maintenance)
        ai_panel = self._build_ai_panel(machines, anomalies, predictions)

        # 4. Self-healing (uses exact fields: action, action_description, rl_votes, triggered_by)
        self._process_healing(machines, healing_actions)

        # 5. Cyber events (uses exact fields: threat_type, severity, target_machine)
        for threat in cyber_events.get("threats", []):
            self.log.append("CYBER",
                f"Threat: {threat.get('threat_type','?')} → "
                f"{threat.get('target_machine','network')} "
                f"· sev:{threat.get('severity','?')} "
                f"· conf:{threat.get('confidence',0)*100:.0f}%",
                machine_id=threat.get("target_machine"), phase="AI")

        # 6. Efficiency (factory_efficiency_score from efficiency_score module)
        efficiency = factory_state.get("efficiency", {})
        eff_score  = efficiency.get("factory_efficiency_score") if efficiency else None
        if eff_score is not None and self._tick % 10 == 1:
            self.log.append("OPTIM",
                f"Factory efficiency: {eff_score:.1f}% · Grade: {efficiency.get('grade','?')}",
                phase="AI")

        # 7. Response panel
        response_panel = {
            "latest_actions": self.response_tracker.get_all_latest(),
            "history":        self.response_tracker.get_history(12),
        }

        # 8. Pipeline stage
        pipeline = self._pipeline(anomalies, healing_actions, cyber_events)

        # 9. Summary
        summary = {
            "factory_status":   factory.get("status", "running"),
            "tick":             self._tick,
            "throughput":       factory.get("current_throughput", 0),
            "bottleneck":       factory.get("bottleneck_machine"),
            "active_scenarios": active_scenarios,
            "anomaly_count":    len(anomalies),
            "healing_count":    len(healing_actions),
            "efficiency_score": eff_score,
            "timestamp":        datetime.utcnow().isoformat(),
        }

        return {
            "type":           "d2_tick",
            "sensor_panel":   sensor_panel,
            "ai_panel":       ai_panel,
            "terminal_log":   self.log.get_recent(80),
            "response_panel": response_panel,
            "pipeline":       pipeline,
            "summary":        summary,
            "tick":           self._tick,
        }

    # ── Sensor panel ──────────────────────────────────────────────────────────

    def _build_sensor_panel(self, machines: Dict) -> Dict:
        panel = {}
        for mid, mdata in machines.items():
            sensors = mdata.get("sensors", {})
            status  = (mdata.get("status", "normal") or "normal").lower()
            health  = mdata.get("health_score", 100.0)
            prev    = self._prev_sensors.get(mid, sensors)

            # Status-change log
            prev_st = self._last_statuses.get(mid, "normal")
            if status != prev_st:
                if status in ("warning", "critical", "failure"):
                    self.log.append(
                        "WARN" if status == "warning" else "CRITICAL",
                        f"{mid} state: {prev_st.upper()} → {status.upper()} "
                        f"| T={sensors.get('temperature',0):.1f}°C "
                        f"V={sensors.get('vibration',0):.2f}mm/s",
                        machine_id=mid, phase="PHYSICAL")
                elif status in ("normal", "healing") and prev_st in ("warning","critical","failure"):
                    self.log.append("RESPONSE",
                        f"{mid} recovered to {status.upper()} — sensors normalising",
                        machine_id=mid, phase="RESPONSE")
                self._last_statuses[mid] = status

            # Periodic sensor log when faulted
            if self._tick % 5 == 0 and status in ("warning", "critical"):
                self.log.append("SENSOR",
                    f"{mid}  T:{sensors.get('temperature',0):.1f}°C  "
                    f"V:{sensors.get('vibration',0):.2f}mm/s  "
                    f"I:{sensors.get('motor_current',0):.1f}A  "
                    f"S:{sensors.get('speed',0):.0f}RPM",
                    machine_id=mid, phase="PHYSICAL")

            # Deltas
            deltas = {k: round(sensors.get(k, 0) - prev.get(k, 0), 3)
                      for k in ["temperature","vibration","motor_current","speed","load"]}

            # Per-sensor alert level
            sensor_alerts = {k: _slevel(sensors.get(k, 0), k) for k in THRESHOLDS}

            # Update sparkline history
            hist = self._sensor_history.get(mid, {})
            for key in ["temperature","vibration","motor_current","speed","load"]:
                if key in hist:
                    hist[key].append(round(sensors.get(key, 0), 3))
            if "health_score" in hist:
                hist["health_score"].append(round(health, 1))

            panel[mid] = {
                "machine_id":    mid,
                "name":          MACHINE_NAMES.get(mid, mid),
                "status":        status,
                "health":        round(health, 1),
                "sensors":       {k: round(v, 3) for k, v in sensors.items()},
                "deltas":        deltas,
                "sensor_alerts": sensor_alerts,
                "is_healing":    mdata.get("is_healing", False),
                "fault_code":    mdata.get("fault_code"),
                "degradation":   round(mdata.get("degradation_level", 0), 4),
                "history":       {k: list(v) for k, v in hist.items()},
            }
            self._prev_sensors[mid] = dict(sensors)
        return panel

    # ── AI regulation panel ───────────────────────────────────────────────────

    def _build_ai_panel(self, machines: Dict, anomalies: List[Dict],
                         predictions: List[Dict]) -> Dict:
        # Exact field: machine_id from both modules
        anomaly_map    = {a["machine_id"]: a for a in anomalies}
        prediction_map = {p["machine_id"]: p for p in predictions}
        panel = {}

        for mid, mdata in machines.items():
            sensors = mdata.get("sensors", {})
            status  = (mdata.get("status", "normal") or "normal").lower()
            health  = mdata.get("health_score", 100.0)

            # ── anomaly_detection fields ──────────────────────────────────
            # composite_score (NOT anomaly_score)
            # detector_votes, detector_results, sensor_deviations
            anom            = anomaly_map.get(mid, {})
            is_anomaly      = bool(anom)
            composite_score = anom.get("composite_score", 0.0)
            anomaly_type    = anom.get("anomaly_type", "NONE")
            severity        = anom.get("severity", "low")
            detector_votes  = anom.get("detector_votes", 0)
            detector_results = anom.get("detector_results", {})
            sensor_devs     = anom.get("sensor_deviations", {})

            # contributing sensors = those with >10% deviation
            contributing = [k for k, v in sensor_devs.items() if abs(v) > 10.0]

            # ── predictive_maintenance fields ─────────────────────────────
            # failure_probability, rul_hours, model_predictions,
            # contributing_sensors, alert_level, recommendation
            pred           = prediction_map.get(mid, {})
            failure_prob   = pred.get("failure_probability", 0.0)
            rul_hours      = pred.get("rul_hours")
            alert_level    = pred.get("alert_level", "low")
            recommendation = pred.get("recommendation", "")
            model_preds    = pred.get("model_predictions", {})
            pred_contrib   = pred.get("contributing_sensors", [])
            pred_sensors   = [c.get("sensor") for c in pred_contrib if isinstance(c, dict)]
            all_triggered  = list(set(contributing + pred_sensors))

            # Which detectors fired (from detector_results)
            models_fired = []
            if detector_results.get("autoencoder", {}).get("detected"):
                models_fired.append("Autoencoder")
            if detector_results.get("isolation_forest", {}).get("detected"):
                models_fired.append("Isolation Forest")
            if detector_results.get("lstm", {}).get("detected"):
                models_fired.append("LSTM")
            if "tcn" in model_preds:
                models_fired.append("TCN")
            if "tft_median" in model_preds:
                models_fired.append("TFT")
            if not models_fired:
                models_fired = ["Threshold", "Statistical"]

            model_conf = max(
                model_preds.get("tft_median", failure_prob),
                model_preds.get("lstm", failure_prob), 0.0
            ) if model_preds else 0.85

            decision = self._ai_decision(severity, failure_prob, all_triggered, status)

            regulation = {
                "machine_id": mid,
                "name":       MACHINE_NAMES.get(mid, mid),
                "status":     status,
                "input": {
                    "temperature":   sensors.get("temperature",   0),
                    "vibration":     sensors.get("vibration",     0),
                    "motor_current": sensors.get("motor_current", 0),
                    "speed":         sensors.get("speed",         0),
                    "load":          sensors.get("load",          0),
                    "health":        health,
                },
                "process": {
                    "is_anomaly":        is_anomaly,
                    "anomaly_type":      anomaly_type,
                    "anomaly_score":     round(composite_score, 4),  # composite_score
                    "severity":          severity,
                    "failure_prob":      round(failure_prob, 4),
                    "rul_hours":         round(rul_hours, 1) if rul_hours else None,
                    "alert_level":       alert_level,
                    "recommendation":    recommendation,
                    "model_confidence":  round(model_conf, 3),
                    "models_fired":      models_fired,
                    "contributing":      all_triggered,
                    "trend_direction":   "rising" if composite_score > 0.3 else "stable",
                    "detector_votes":    detector_votes,
                    "model_predictions": model_preds,
                    "sensor_deviations": sensor_devs,
                },
                "decision": decision,
            }

            self.ai_tracker.update(mid, regulation)
            panel[mid] = regulation

            # Terminal log
            if is_anomaly and severity in ("high", "critical"):
                self.log.append("AI",
                    f"Anomaly [{anomaly_type}] score={composite_score:.3f} "
                    f"sev={severity.upper()} · votes:{detector_votes}/3",
                    machine_id=mid, phase="AI")
            if failure_prob > 0.50:
                rul_s = f"RUL≈{rul_hours:.1f}h" if rul_hours else "RUL:?"
                self.log.append("AI",
                    f"Predictive: {failure_prob*100:.0f}% failure probability · {rul_s}",
                    machine_id=mid, phase="AI")
            if decision["action"] not in ("NOMINAL", "MONITOR"):
                self.log.append("DECISION",
                    f"AI Decision → {decision['action']} "
                    f"(conf:{decision['confidence']*100:.0f}%): {decision['reason']}",
                    machine_id=mid, phase="DECISION")

        return panel

    # ── Self-healing ──────────────────────────────────────────────────────────

    def _process_healing(self, machines: Dict, healing_actions: List[Dict]) -> None:
        """
        Uses exact self_healing fields:
          action, action_description, confidence, triggered_by, rl_votes
        """
        for action in healing_actions:
            mid  = action.get("machine_id", "?")
            act  = action.get("action", "?")
            # action_description is the exact field from SelfHealingController
            desc = action.get("action_description",
                   action.get("description", "AI-triggered control"))
            mdata  = machines.get(mid, {})
            sensors = mdata.get("sensors", {})

            if not self._healing_active.get(mid):
                self._before_healing[mid] = dict(sensors)
                self._healing_active[mid] = True

                # Log real RL ensemble votes (rl_votes field)
                rl_votes = action.get("rl_votes", {})
                if rl_votes:
                    vs = "  ".join(
                        f"{k.upper()}:{v.get('action','?')}({v.get('confidence',0)*100:.0f}%)"
                        for k, v in rl_votes.items()
                    )
                    self.log.append("AI",
                        f"RL ensemble [{mid}]: {vs}",
                        machine_id=mid, phase="AI")

                self.log.append("CONTROL",
                    f"Command → {mid}: [{act.replace('_',' ').upper()}] {desc}",
                    machine_id=mid, phase="CONTROL")
                self.log.append("TWIN",
                    f"Digital twin updated → {act} applied on {mid}",
                    machine_id=mid, phase="CONTROL")

        # Check for resolved healing
        for mid, was_healing in list(self._healing_active.items()):
            if not was_healing:
                continue
            mdata   = machines.get(mid, {})
            status  = (mdata.get("status", "normal") or "normal").lower()
            is_heal = mdata.get("is_healing", False)

            if is_heal:
                sensors = mdata.get("sensors", {})
                before  = self._before_healing.get(mid, sensors)
                diff    = sensors.get("temperature", 0) - before.get("temperature", 0)
                if abs(diff) > 1.5 and self._tick % 3 == 0:
                    direction = "decreasing ↓" if diff < 0 else "still elevated ↑"
                    self.log.append("RESPONSE",
                        f"Physical response — Temp {direction} "
                        f"({before.get('temperature',0):.1f} → "
                        f"{sensors.get('temperature',0):.1f}°C)",
                        machine_id=mid, phase="RESPONSE")

            elif status in ("normal", "warning") and self._healing_active.get(mid):
                sensors = mdata.get("sensors", {})
                before  = self._before_healing.get(mid, sensors)
                rec = self.response_tracker.record_action(
                    machine_id=mid,
                    action="SELF_HEALING_COMPLETE",
                    before=before, after=dict(sensors),
                    cause="AI autonomous control (PPO/SAC/DQN ensemble)",
                    severity="resolved",
                )
                self.log.append("RESPONSE",
                    f"✅ {mid} stabilised — health:{mdata.get('health_score',0):.0f}% "
                    f"· improvement:{rec['improvement']:.1f}%",
                    machine_id=mid, phase="RESPONSE")
                self._healing_active[mid] = False
                self._before_healing.pop(mid, None)

    # ── Pipeline stage ────────────────────────────────────────────────────────

    def _pipeline(self, anomalies: List, healing_actions: List,
                  cyber_events: Dict) -> Dict:
        stages = [
            {"id": "physical",  "label": "PHYSICAL DATA",   "icon": "📡"},
            {"id": "ai",        "label": "AI ANALYSIS",      "icon": "🤖"},
            {"id": "decision",  "label": "DECISION",          "icon": "⚡"},
            {"id": "control",   "label": "CONTROL ACTION",   "icon": "⚙"},
            {"id": "twin",      "label": "TWIN UPDATE",       "icon": "🌐"},
            {"id": "response",  "label": "PHYS RESPONSE",    "icon": "🌍"},
        ]
        if healing_actions:                 active = "control"
        elif anomalies:                     active = "ai"
        elif cyber_events.get("threats"):   active = "ai"
        else:                               active = "physical"

        order = [s["id"] for s in stages]
        ai    = order.index(active)
        for i, s in enumerate(stages):
            s["state"] = "done" if i < ai else ("active" if i == ai else "pending")
        return {"stages": stages, "active": active}

    # ── AI decision mapping ───────────────────────────────────────────────────

    @staticmethod
    def _ai_decision(severity: str, failure_prob: float,
                     triggered: List[str], status: str) -> Dict:
        status = (status or "normal").lower()
        if status == "failure" or (severity == "critical" and failure_prob > 0.80):
            return {"action": "EMERGENCY SHUTDOWN", "urgency": "IMMEDIATE",
                    "confidence": 0.97,
                    "reason": "Catastrophic failure imminent — prevent equipment damage"}
        if severity == "critical" or failure_prob > 0.70:
            if "temperature" in triggered:
                return {"action": "ACTIVATE COOLING + REDUCE LOAD", "urgency": "HIGH",
                        "confidence": 0.91,
                        "reason": "Thermal runaway risk — cooling required immediately"}
            if "vibration" in triggered:
                return {"action": "REDUCE SPEED 30%", "urgency": "HIGH",
                        "confidence": 0.88,
                        "reason": "Bearing stress — speed reduction prevents failure"}
            return {"action": "REDUCE LOAD 35%", "urgency": "HIGH",
                    "confidence": 0.85,
                    "reason": "Critical anomaly — load shedding initiated"}
        if severity == "high" or failure_prob > 0.45:
            return {"action": "REDUCE SPEED 20%", "urgency": "MEDIUM",
                    "confidence": 0.76,
                    "reason": "Anomaly trending — precautionary speed reduction"}
        if severity == "medium" or failure_prob > 0.20:
            return {"action": "MONITOR CLOSELY", "urgency": "LOW",
                    "confidence": 0.65,
                    "reason": "Early-warning sensors elevated — poll rate increased"}
        return {"action": "NOMINAL", "urgency": "NONE",
                "confidence": 0.99,
                "reason": "All sensors within normal operating bounds"}

    # ── REST helpers ──────────────────────────────────────────────────────────

    def get_log_since(self, seq: int) -> List[Dict]:
        return self.log.get_since(seq)

    def get_full_log(self, n: int = 100) -> List[Dict]:
        return self.log.get_recent(n)

    def get_ai_panel(self) -> Dict:
        return self.ai_tracker.get_all()

    def get_response_panel(self) -> Dict:
        return {
            "latest":  self.response_tracker.get_all_latest(),
            "history": self.response_tracker.get_history(15),
        }
