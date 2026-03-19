"""
SentinelTwin AI — REST API Routes
Full REST endpoint coverage for all platform modules.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["SentinelTwin API"])


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ScenarioRequest(BaseModel):
    scenario_type: str
    machine_id: Optional[str] = None
    intensity: Optional[float] = 1.0
    duration_seconds: Optional[int] = 30


class CyberAttackRequest(BaseModel):
    attack_type: str
    target_machine: Optional[str] = None
    intensity: Optional[float] = 1.0


class MachineCommandRequest(BaseModel):
    machine_id: str
    command: str
    value: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY STATE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/factory/state")
async def get_factory_state(request: Request) -> Dict[str, Any]:
    """Return the complete current factory state for all machines."""
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    state["timestamp"] = datetime.utcnow().isoformat()
    return state


@router.get("/factory/machines")
async def get_all_machines(request: Request) -> Dict[str, Any]:
    """Return metadata and current readings for all 5 machines."""
    simulation = request.app.state.simulation
    return {"machines": simulation.get_machine_list()}


@router.get("/factory/machines/{machine_id}")
async def get_machine(machine_id: str, request: Request) -> Dict[str, Any]:
    """Return detailed information for a specific machine."""
    simulation = request.app.state.simulation
    machine = simulation.get_machine_detail(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return machine


@router.get("/factory/machines/{machine_id}/history")
async def get_machine_history(machine_id: str, request: Request, limit: int = 50) -> Dict[str, Any]:
    """Return sensor history for a specific machine."""
    simulation = request.app.state.simulation
    history = simulation.get_machine_history(machine_id, limit)
    return {"machine_id": machine_id, "history": history}


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTIVE MAINTENANCE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/maintenance/predictions")
async def get_all_predictions(request: Request) -> Dict[str, Any]:
    """Return current failure predictions for all machines."""
    pm = request.app.state.predictive_maintenance
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    predictions = pm.predict(state)
    return {"predictions": predictions, "timestamp": datetime.utcnow().isoformat()}


@router.get("/maintenance/predictions/{machine_id}")
async def get_machine_prediction(machine_id: str, request: Request) -> Dict[str, Any]:
    """Return failure prediction for a specific machine."""
    pm = request.app.state.predictive_maintenance
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    predictions = pm.predict(state)
    machine_pred = next((p for p in predictions if p["machine_id"] == machine_id), None)
    if not machine_pred:
        raise HTTPException(status_code=404, detail=f"No prediction for machine {machine_id}")
    return machine_pred


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY DETECTION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/anomalies/current")
async def get_current_anomalies(request: Request) -> Dict[str, Any]:
    """Return currently detected anomalies."""
    anomaly_detector = request.app.state.anomaly_detector
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    anomalies = anomaly_detector.detect(state)
    return {"anomalies": anomalies, "count": len(anomalies), "timestamp": datetime.utcnow().isoformat()}


@router.get("/anomalies/history")
async def get_anomaly_history(request: Request, limit: int = 50) -> Dict[str, Any]:
    """Return recent anomaly history."""
    anomaly_detector = request.app.state.anomaly_detector
    return {"history": anomaly_detector.get_history(limit)}


# ─────────────────────────────────────────────────────────────────────────────
# CYBERSECURITY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/cybersecurity/status")
async def get_cyber_status(request: Request) -> Dict[str, Any]:
    """Return current cybersecurity status."""
    cybersecurity = request.app.state.cybersecurity
    return cybersecurity.get_status()


@router.get("/cybersecurity/threats")
async def get_threats(request: Request, limit: int = 20) -> Dict[str, Any]:
    """Return recent cyber threat history."""
    cybersecurity = request.app.state.cybersecurity
    return {"threats": cybersecurity.get_threat_history(limit)}


@router.post("/cybersecurity/simulate-attack")
async def simulate_cyber_attack(attack: CyberAttackRequest, request: Request) -> Dict[str, Any]:
    """Trigger a simulated cyber attack for demonstration/testing."""
    cybersecurity = request.app.state.cybersecurity
    simulation = request.app.state.simulation
    result = cybersecurity.simulate_attack(
        attack_type=attack.attack_type,
        target_machine=attack.target_machine,
        intensity=attack.intensity,
        simulation=simulation,
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ROOT CAUSE ANALYSIS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/rca/{machine_id}")
async def get_root_cause_analysis(machine_id: str, request: Request) -> Dict[str, Any]:
    """Return root cause analysis for a specific machine."""
    rca = request.app.state.root_cause
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    return rca.analyze(machine_id, state)


@router.get("/rca/history")
async def get_rca_history(request: Request, limit: int = 20) -> Dict[str, Any]:
    """Return recent root cause analysis history."""
    rca = request.app.state.root_cause
    return {"history": rca.get_history(limit)}


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION OPTIMIZATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/optimization/recommendations")
async def get_optimization_recommendations(request: Request) -> Dict[str, Any]:
    """Return current production optimization recommendations."""
    optimizer = request.app.state.production_optimizer
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    return optimizer.optimize(state)


@router.get("/optimization/efficiency")
async def get_efficiency_score(request: Request) -> Dict[str, Any]:
    """Return the current factory efficiency score."""
    scorer = request.app.state.efficiency_scorer
    simulation = request.app.state.simulation
    state = simulation.get_current_state()
    return scorer.compute(state)


# ─────────────────────────────────────────────────────────────────────────────
# LIFECYCLE MONITORING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/lifecycle")
async def get_all_lifecycle(request: Request) -> Dict[str, Any]:
    """Return lifecycle data for all machines."""
    lifecycle = request.app.state.lifecycle_monitor
    return {"lifecycle": lifecycle.get_all_lifecycle()}


@router.get("/lifecycle/{machine_id}")
async def get_machine_lifecycle(machine_id: str, request: Request) -> Dict[str, Any]:
    """Return lifecycle data for a specific machine."""
    lifecycle = request.app.state.lifecycle_monitor
    data = lifecycle.get_lifecycle(machine_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"No lifecycle data for {machine_id}")
    return data


# ─────────────────────────────────────────────────────────────────────────────
# INCIDENT TIMELINE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/incidents")
async def get_incidents(request: Request, limit: int = 50) -> Dict[str, Any]:
    """Return the incident timeline."""
    timeline = request.app.state.incident_timeline
    return {"events": timeline.get_recent(limit), "total": timeline.get_total_count()}


@router.delete("/incidents/clear")
async def clear_incidents(request: Request) -> Dict[str, Any]:
    """Clear all incident records."""
    timeline = request.app.state.incident_timeline
    timeline.clear()
    return {"status": "cleared", "timestamp": datetime.utcnow().isoformat()}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO ENGINE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/scenarios")
async def get_scenarios(request: Request) -> Dict[str, Any]:
    """Return available and active scenarios."""
    scenario_engine = request.app.state.scenario_engine
    return {
        "available": scenario_engine.get_available_scenarios(),
        "active": scenario_engine.get_active_scenarios(),
    }


@router.post("/scenarios/trigger")
async def trigger_scenario(scenario_req: ScenarioRequest, request: Request) -> Dict[str, Any]:
    """Trigger a factory scenario for demonstration/testing."""
    scenario_engine = request.app.state.scenario_engine
    result = scenario_engine.trigger(
        scenario_type=scenario_req.scenario_type,
        machine_id=scenario_req.machine_id,
        intensity=scenario_req.intensity,
        duration_seconds=scenario_req.duration_seconds,
    )
    return result


@router.post("/scenarios/stop/{scenario_id}")
async def stop_scenario(scenario_id: str, request: Request) -> Dict[str, Any]:
    """Stop a running scenario."""
    scenario_engine = request.app.state.scenario_engine
    result = scenario_engine.stop(scenario_id)
    return result


@router.post("/scenarios/stop-all")
async def stop_all_scenarios(request: Request) -> Dict[str, Any]:
    """Stop all active scenarios."""
    scenario_engine = request.app.state.scenario_engine
    result = scenario_engine.stop_all()
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MACHINE CONTROL ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/machines/command")
async def send_machine_command(command: MachineCommandRequest, request: Request) -> Dict[str, Any]:
    """Send a control command to a specific machine."""
    simulation = request.app.state.simulation
    result = simulation.apply_command(
        machine_id=command.machine_id,
        command=command.command,
        value=command.value,
    )
    return result


@router.post("/machines/{machine_id}/reset")
async def reset_machine(machine_id: str, request: Request) -> Dict[str, Any]:
    """Reset a machine to normal operating state."""
    simulation = request.app.state.simulation
    result = simulation.reset_machine(machine_id)
    return result


@router.post("/factory/reset")
async def reset_factory(request: Request) -> Dict[str, Any]:
    """Reset entire factory to normal operating state."""
    simulation = request.app.state.simulation
    scenario_engine = request.app.state.scenario_engine
    scenario_engine.stop_all()
    simulation.reset_all_machines()
    return {"status": "reset", "timestamp": datetime.utcnow().isoformat()}


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM INFO ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/system/info")
async def get_system_info(request: Request) -> Dict[str, Any]:
    """Return system information and connection stats."""
    from sentinelcore.websocket_manager import manager
    return {
        "platform": "SentinelTwin AI",
        "version": "1.0.0",
        "factory_name": "SentinelTwin Smart Factory",
        "machine_count": 5,
        "modules": [
            "Predictive Maintenance AI",
            "Anomaly Detection AI",
            "Defect Detection Vision AI",
            "AI Failure Explanation Engine",
            "Cybersecurity Intelligence",
            "Industrial IDS",
            "Cyber Attack Simulation",
            "Automated Cyber Response",
            "Root Cause Analysis AI",
            "Self-Healing Autonomous Control",
            "Production Optimization AI",
            "Factory Efficiency Score",
            "Machine Lifecycle Monitoring",
            "Smart Alert Prioritization",
            "AI Incident Timeline",
            "Scenario Simulation System",
            "3D Digital Twin",
        ],
        "websocket_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/system/connections")
async def get_connections(request: Request) -> Dict[str, Any]:
    """Return WebSocket connection statistics."""
    from sentinelcore.websocket_manager import manager
    return manager.get_connection_stats()
