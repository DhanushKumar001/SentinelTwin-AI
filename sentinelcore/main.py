"""
SentinelTwin AI — Main Application Entry Point
FastAPI + WebSocket + full simulation loop using all given modules.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from sentinelcore.config import APP, SIMULATION
from sentinelcore.websocket_manager import manager

logging.basicConfig(
    level=getattr(logging, APP.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentineltwin")

# ── Module globals ────────────────────────────────────────────────────────────
_simulation            = None
_anomaly_detector      = None
_predictive_maintenance= None
_failure_explanation   = None
_defect_detector       = None
_cybersecurity         = None
_root_cause            = None
_self_healing          = None
_production_optimizer  = None
_efficiency_scorer     = None
_lifecycle_monitor     = None
_alert_prioritizer     = None
_incident_timeline     = None
_scenario_engine       = None
_d2_engine             = None
_simulation_task: asyncio.Task = None


async def _run_simulation_loop():
    global _simulation, _anomaly_detector, _predictive_maintenance
    global _failure_explanation, _defect_detector, _cybersecurity
    global _root_cause, _self_healing, _production_optimizer
    global _efficiency_scorer, _lifecycle_monitor, _alert_prioritizer
    global _incident_timeline, _scenario_engine, _d2_engine

    logger.info("Starting SentinelTwin simulation loop...")
    tick_count = 0

    while True:
        try:
            tick_start = asyncio.get_event_loop().time()

            # 1. FactorySimulation.tick()
            factory_state = _simulation.tick()
            tick_count += 1

            # 2. ScenarioEngine.tick_all()
            _scenario_engine.tick_all()

            # 3. LifecycleMonitor.update()
            _lifecycle_monitor.update(factory_state)

            # 4. AnomalyDetector.detect()
            anomalies = _anomaly_detector.detect(factory_state)
            if anomalies:
                for anomaly in anomalies:
                    await manager.broadcast_anomaly(anomaly)
                    _incident_timeline.add_event(
                        event_type="anomaly",
                        description=f"Anomaly on {anomaly['machine_id']}: {anomaly['anomaly_type']}",
                        severity=anomaly.get("severity", "medium"),
                        machine_id=anomaly["machine_id"],
                    )

            # 5. PredictiveMaintenance.predict()
            predictions = _predictive_maintenance.predict(factory_state)
            for pred in predictions:
                if pred["failure_probability"] > 0.40:
                    explanation = _failure_explanation.explain(pred, factory_state)
                    pred["explanation"] = explanation
                    await manager.broadcast_prediction(pred)
                    if pred["failure_probability"] > 0.70:
                        _incident_timeline.add_event(
                            event_type="predictive_alert",
                            description=f"Predictive alert on {pred['machine_id']}: {pred['failure_probability']*100:.0f}% failure prob",
                            severity="high" if pred["failure_probability"] < 0.85 else "critical",
                            machine_id=pred["machine_id"],
                        )

            # 6. DefectDetectionAI.detect() every 5 ticks
            latest_defect = {}
            if tick_count % 5 == 0:
                defect_result = _defect_detector.detect(factory_state)
                latest_defect = defect_result
                if defect_result.get("defect_found"):
                    await manager.broadcast_defect(defect_result)
                    _incident_timeline.add_event(
                        event_type="defect",
                        description=f"Defect: {defect_result.get('defect_type')} (conf:{defect_result.get('confidence',0)*100:.0f}%)",
                        severity="high", machine_id="M3",
                    )

            # 7. CybersecurityIntelligence.monitor()
            cyber_events = _cybersecurity.monitor(factory_state, tick_count)
            for threat in cyber_events.get("threats", []):
                await manager.broadcast_cyber_threat(threat)
                response = _cybersecurity.auto_respond(threat)
                await manager.broadcast_cyber_response(response)
                _incident_timeline.add_event(
                    event_type="cyber_threat",
                    description=f"Cyber threat: {threat['threat_type']} on {threat.get('target_machine','network')}",
                    severity=threat.get("severity", "critical"),
                    machine_id=threat.get("target_machine"),
                )

            # 8. SelfHealingController.evaluate_and_act()
            healing_actions = _self_healing.evaluate_and_act(factory_state, anomalies, predictions)
            for action in healing_actions:
                await manager.broadcast_self_healing(action)
                _incident_timeline.add_event(
                    event_type="self_healing",
                    description=f"Self-healing: {action['action']} on {action['machine_id']}",
                    severity="info", machine_id=action["machine_id"],
                )
                _simulation.apply_healing_action(action)

            # 9. RootCauseAnalyzer.analyze()
            rca_results = {}
            for machine_id, machine_data in factory_state["machines"].items():
                if machine_data["status"] in ("critical", "failure"):
                    rca = _root_cause.analyze(machine_id, factory_state)
                    rca_results[machine_id] = rca
                    if rca.get("analysis_triggered"):
                        await manager.broadcast_root_cause(rca)

            # 10. ProductionOptimizer.optimize() every 10 ticks
            if tick_count % 10 == 0:
                optimization = _production_optimizer.optimize(factory_state)
                await manager.broadcast_optimization(optimization)

            # 11. EfficiencyScorer.compute() every 5 ticks
            if tick_count % 5 == 0:
                efficiency = _efficiency_scorer.compute(factory_state)
                await manager.broadcast_efficiency_score(efficiency)

            # 12. AlertPrioritizer.process_and_prioritize()
            alerts = _alert_prioritizer.process_and_prioritize(
                anomalies, predictions, cyber_events.get("threats", [])
            )
            for alert in alerts:
                await manager.broadcast_alert(alert)

            # 13. Compose factory state payload for Dashboard 1
            factory_state["lifecycle"]        = _lifecycle_monitor.get_all_lifecycle()
            factory_state["efficiency"]       = _efficiency_scorer.get_latest()
            factory_state["active_scenarios"] = _scenario_engine.get_active_scenarios()
            factory_state["tick"]             = tick_count
            factory_state["latest_defect"]    = latest_defect
            factory_state["rca_results"]      = rca_results
            await manager.broadcast_sensor_update(factory_state)

            # 14. Incident timeline every 3 ticks
            if tick_count % 3 == 0:
                await manager.broadcast_incident({"events": _incident_timeline.get_recent(20)})

            # 15. Dashboard 2 — process tick & broadcast to /ws/d2
            if _d2_engine is not None:
                try:
                    d2_payload = _d2_engine.process_tick(
                        factory_state=factory_state,
                        anomalies=anomalies,
                        predictions=predictions,
                        healing_actions=healing_actions,
                        cyber_events=cyber_events,
                        active_scenarios=_scenario_engine.get_active_scenarios(),
                    )
                    await manager.broadcast_d2(d2_payload)
                except Exception as d2_err:
                    logger.warning(f"Dashboard 2 tick error: {d2_err}")

            elapsed    = asyncio.get_event_loop().time() - tick_start
            sleep_time = max(0.0, SIMULATION.tick_interval - elapsed)
            await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Simulation loop error: {e}", exc_info=True)
            await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _simulation, _anomaly_detector, _predictive_maintenance
    global _failure_explanation, _defect_detector, _cybersecurity
    global _root_cause, _self_healing, _production_optimizer
    global _efficiency_scorer, _lifecycle_monitor, _alert_prioritizer
    global _incident_timeline, _scenario_engine, _d2_engine
    global _simulation_task

    logger.info("Initialising SentinelTwin AI modules...")

    from sentinelcore.modules.factory_simulation      import FactorySimulation
    from sentinelcore.modules.anomaly_detection       import AnomalyDetector
    from sentinelcore.modules.predictive_maintenance  import PredictiveMaintenance
    from sentinelcore.modules.failure_explanation     import FailureExplanationEngine
    from sentinelcore.modules.defect_detection        import DefectDetectionAI
    from sentinelcore.modules.cybersecurity           import CybersecurityIntelligence
    from sentinelcore.modules.root_cause_analysis     import RootCauseAnalyzer
    from sentinelcore.modules.self_healing            import SelfHealingController
    from sentinelcore.modules.production_optimization import ProductionOptimizer
    from sentinelcore.modules.efficiency_score        import EfficiencyScorer
    from sentinelcore.modules.lifecycle_monitoring    import LifecycleMonitor
    from sentinelcore.modules.alert_prioritization    import AlertPrioritizer
    from sentinelcore.modules.incident_timeline       import IncidentTimeline
    from sentinelcore.modules.scenario_engine         import ScenarioEngine
    from sentinelcore.modules.dashboard2_engine       import Dashboard2Engine

    _simulation            = FactorySimulation()
    _anomaly_detector      = AnomalyDetector()
    _predictive_maintenance= PredictiveMaintenance()
    _failure_explanation   = FailureExplanationEngine()
    _defect_detector       = DefectDetectionAI()
    _cybersecurity         = CybersecurityIntelligence()
    _root_cause            = RootCauseAnalyzer()
    _self_healing          = SelfHealingController()
    _production_optimizer  = ProductionOptimizer()
    _efficiency_scorer     = EfficiencyScorer()
    _lifecycle_monitor     = LifecycleMonitor()
    _alert_prioritizer     = AlertPrioritizer()
    _incident_timeline     = IncidentTimeline()
    _scenario_engine       = ScenarioEngine(_simulation)
    _d2_engine             = Dashboard2Engine()

    app.state.simulation             = _simulation
    app.state.scenario_engine        = _scenario_engine
    app.state.incident_timeline      = _incident_timeline
    app.state.lifecycle_monitor      = _lifecycle_monitor
    app.state.efficiency_scorer      = _efficiency_scorer
    app.state.cybersecurity          = _cybersecurity
    app.state.root_cause             = _root_cause
    app.state.production_optimizer   = _production_optimizer
    app.state.predictive_maintenance = _predictive_maintenance
    app.state.anomaly_detector       = _anomaly_detector
    app.state.defect_detector        = _defect_detector
    app.state.failure_explanation    = _failure_explanation
    app.state.self_healing           = _self_healing
    app.state.alert_prioritizer      = _alert_prioritizer
    app.state.d2_engine              = _d2_engine

    logger.info("All AI modules initialised successfully.")
    _simulation_task = asyncio.create_task(_run_simulation_loop())
    logger.info(f"SentinelTwin AI Platform started on {APP.host}:{APP.port}")
    yield

    logger.info("Shutting down...")
    if _simulation_task and not _simulation_task.done():
        _simulation_task.cancel()
        try:
            await _simulation_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete.")


app = FastAPI(
    title="SentinelTwin AI",
    description="Industry 4.0 Autonomous Smart Factory Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sentinelcore.api.routes            import router as api_router
from sentinelcore.api.websocket_handler import ws_router
from sentinelcore.api.dashboard2_routes import d2_router, d2_ws_router

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
app.include_router(d2_router)
app.include_router(d2_ws_router)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "sentinelui")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy", "service": "SentinelTwin AI", "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "connections": manager.get_connection_count(),
        "d2_connections": len(manager.d2_connections),
        "modules": [
            "factory_simulation","anomaly_detection","predictive_maintenance",
            "failure_explanation","defect_detection","cybersecurity",
            "root_cause_analysis","self_healing","production_optimization",
            "efficiency_score","lifecycle_monitoring","alert_prioritization",
            "incident_timeline","scenario_engine","dashboard2_engine",
        ],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found", "path": str(request.url.path)})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
