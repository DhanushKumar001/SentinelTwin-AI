"""
SentinelTwin AI — Cybersecurity Intelligence Module
Industrial Network Anomaly Detection, IDS, Cyber Attack Simulation,
and Automated Cyber Response System.
"""

import random
import ipaddress
from collections import deque, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import CyberThreatType, AlertLevel, MachineStatus, MACHINES


# Known safe IP ranges for the simulated industrial network
SAFE_IP_RANGES = ["192.168.1.", "10.0.0.", "172.16.0."]
KNOWN_MALICIOUS_IPS = ["203.0.113.", "198.51.100.", "192.0.2."]

# PLC command whitelist (normal industrial commands)
SAFE_PLC_COMMANDS = [
    "START_CONVEYOR", "STOP_CONVEYOR", "SET_SPEED", "READ_SENSOR",
    "RESET_ALARM", "STATUS_REQUEST", "HEARTBEAT", "DATA_POLL",
]

# Attack signatures for IDS detection
ATTACK_SIGNATURES = {
    CyberThreatType.COMMAND_INJECTION: {
        "indicators": ["EXEC_CMD", "OVERRIDE_LIMIT", "BYPASS_SAFETY", "SHELL_CMD"],
        "severity": "critical",
        "description": "Unauthorized command injection into PLC",
    },
    CyberThreatType.NETWORK_FLOODING: {
        "indicators": ["PACKET_BURST > 5000/s", "SYN_FLOOD", "UDP_FLOOD", "ICMP_FLOOD"],
        "severity": "high",
        "description": "Network flooding / DDoS attack on industrial network",
    },
    CyberThreatType.UNAUTHORIZED_CONTROL: {
        "indicators": ["UNKNOWN_DEVICE_CMD", "ROGUE_ACTUATOR", "UNAUTHORIZED_WRITE"],
        "severity": "critical",
        "description": "Unauthorized machine control signal detected",
    },
    CyberThreatType.PLC_OVERRIDE: {
        "indicators": ["FORCE_COIL", "DIRECT_WRITE_MEM", "LADDER_OVERRIDE", "FIRMWARE_WRITE"],
        "severity": "critical",
        "description": "PLC override attack — direct memory manipulation",
    },
    CyberThreatType.ABNORMAL_TRAFFIC: {
        "indicators": ["ANOMALOUS_PROTOCOL", "DATA_EXFIL_PATTERN", "C2_BEACON"],
        "severity": "high",
        "description": "Abnormal network traffic pattern — possible data exfiltration",
    },
}


class NetworkAnomalyDetector:
    """
    AI-powered industrial network anomaly detection.
    Monitors packet patterns, device communication, and data flows.
    Uses Isolation Forest and Autoencoder simulation.
    """

    def __init__(self):
        self._baseline_packet_rate: float = 250.0  # packets/second nominal
        self._baseline_bytes_per_second: float = 52000.0
        self._device_communication_map: Dict[str, List[str]] = {
            m.machine_id: [f"PLC_{m.machine_id}", "SCADA_SERVER", "HMI_STATION"]
            for m in MACHINES
        }
        self._known_devices: set = {
            "SCADA_SERVER", "HMI_STATION", "HISTORIAN", "ENG_WORKSTATION",
            "PLC_M1", "PLC_M2", "PLC_M3", "PLC_M4", "PLC_M5",
        }
        self._packet_history: deque = deque(maxlen=100)
        self._anomaly_score_history: deque = deque(maxlen=50)
        self._simulated_tick: int = 0

    def monitor(self, tick: int) -> Dict[str, Any]:
        """
        Simulate network traffic monitoring and anomaly detection.
        Returns network telemetry and any detected anomalies.
        """
        self._simulated_tick = tick

        # Generate simulated network metrics
        noise = random.gauss(0, 15)
        packet_rate = self._baseline_packet_rate + noise
        bytes_per_sec = self._baseline_bytes_per_second + random.gauss(0, 3000)
        active_connections = random.randint(12, 18)

        # Isolation Forest anomaly score
        pkt_deviation = abs(packet_rate - self._baseline_packet_rate) / self._baseline_packet_rate
        bps_deviation = abs(bytes_per_sec - self._baseline_bytes_per_second) / self._baseline_bytes_per_second
        iso_score = min(1.0, (pkt_deviation * 0.6 + bps_deviation * 0.4) * 3.0)

        # Autoencoder reconstruction error
        ae_score = max(0.0, min(1.0, iso_score * 0.8 + random.gauss(0, 0.05)))

        ensemble_score = 0.55 * iso_score + 0.45 * ae_score
        self._anomaly_score_history.append(ensemble_score)

        telemetry = {
            "packet_rate_per_sec": round(packet_rate, 1),
            "bytes_per_sec": round(bytes_per_sec, 1),
            "active_connections": active_connections,
            "known_devices": len(self._known_devices),
            "anomaly_score": round(ensemble_score, 4),
            "isolation_forest_score": round(iso_score, 4),
            "autoencoder_score": round(ae_score, 4),
            "status": "anomalous" if ensemble_score > 0.60 else "normal",
        }

        self._packet_history.append(telemetry)
        return telemetry

    def detect_unknown_device(self) -> Optional[str]:
        """Occasionally simulate an unknown device appearing on the network."""
        if random.random() < 0.02:  # 2% chance per tick
            fake_device = f"UNKNOWN_{random.randint(100, 999)}"
            return fake_device
        return None

    def get_telemetry_history(self, limit: int = 20) -> List[Dict]:
        return list(self._packet_history)[-limit:]


class IndustrialIDS:
    """
    Industrial Intrusion Detection System.
    Monitors PLC commands and machine communication protocols
    for unauthorized control signals and cyber threats.
    """

    def __init__(self):
        self._blocked_ips: set = set()
        self._threat_history: deque = deque(maxlen=200)
        self._detection_count: int = 0
        self._false_positive_rate: float = 0.03

    def analyze_plc_traffic(self, machine_id: str,
                              simulated_attack: Optional[Dict] = None) -> Optional[Dict]:
        """
        Analyze PLC command stream for malicious patterns.
        Returns threat record if detected, None otherwise.
        """
        if simulated_attack:
            return self._create_threat_record(
                machine_id,
                simulated_attack["attack_type"],
                simulated_attack.get("intensity", 1.0),
            )

        # Natural random detection (very low probability in normal operations)
        if random.random() < 0.005:
            attack_type = random.choice([
                CyberThreatType.COMMAND_INJECTION,
                CyberThreatType.ABNORMAL_TRAFFIC,
            ])
            return self._create_threat_record(machine_id, attack_type, 0.5)

        return None

    def _create_threat_record(self, machine_id: str,
                               attack_type: str, intensity: float) -> Dict:
        self._detection_count += 1
        signature = ATTACK_SIGNATURES.get(attack_type, {})
        severity = signature.get("severity", "high")

        # Scale severity with intensity
        if intensity > 0.8 and severity != "critical":
            severity = "critical"
        elif intensity < 0.4 and severity == "critical":
            severity = "high"

        source_ip = random.choice(KNOWN_MALICIOUS_IPS) + str(random.randint(1, 254))
        indicator = random.choice(signature.get("indicators", ["UNKNOWN_SIGNAL"]))

        threat = {
            "threat_id": f"IDS_{self._detection_count:05d}_{datetime.utcnow().strftime('%f')[:6]}",
            "threat_type": attack_type,
            "target_machine": machine_id,
            "severity": severity,
            "source_ip": source_ip,
            "attack_indicator": indicator,
            "description": signature.get("description", "Unknown threat"),
            "intensity": round(intensity, 2),
            "confidence": round(0.75 + intensity * 0.20, 3),
            "packet_count": int(1000 * intensity * random.uniform(0.8, 1.2)),
            "protocol": random.choice(["Modbus/TCP", "EtherNet/IP", "OPC-UA", "PROFINET"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._threat_history.append(threat)
        self._blocked_ips.add(source_ip)
        return threat

    def get_threat_history(self, limit: int = 20) -> List[Dict]:
        return list(self._threat_history)[-limit:]

    def get_blocked_ips(self) -> List[str]:
        return list(self._blocked_ips)


class CybersecurityIntelligence:
    """
    Master cybersecurity intelligence module.
    Orchestrates network anomaly detection, IDS, attack simulation,
    and automated cyber response.
    """

    def __init__(self):
        self._network_monitor = NetworkAnomalyDetector()
        self._ids = IndustrialIDS()
        self._active_attacks: Dict[str, Dict] = {}
        self._response_log: deque = deque(maxlen=100)
        self._isolated_machines: set = set()
        self._threat_level: str = "low"
        self._tick_count: int = 0

    def monitor(self, factory_state: Dict[str, Any],
                 tick_count: int) -> Dict[str, Any]:
        """
        Run full cybersecurity monitoring cycle.
        Returns detected threats.
        """
        self._tick_count = tick_count
        threats = []

        # Network monitoring
        network_telemetry = self._network_monitor.monitor(tick_count)
        unknown_device = self._network_monitor.detect_unknown_device()

        # Check for unknown device — create low-severity threat
        if unknown_device:
            threat = {
                "threat_id": f"IDS_DEV_{tick_count}",
                "threat_type": CyberThreatType.ABNORMAL_TRAFFIC,
                "target_machine": "network",
                "severity": "medium",
                "source_ip": f"10.99.{random.randint(1, 254)}.{random.randint(1, 254)}",
                "attack_indicator": f"Unknown device: {unknown_device}",
                "description": f"Unregistered device {unknown_device} detected on OT network",
                "intensity": 0.4,
                "confidence": 0.81,
                "protocol": "ARP",
                "timestamp": datetime.utcnow().isoformat(),
            }
            threats.append(threat)

        # Process any active simulated attacks through IDS
        for machine_id, attack in list(self._active_attacks.items()):
            if attack.get("ticks_remaining", 0) > 0:
                attack["ticks_remaining"] -= 1
                threat = self._ids.analyze_plc_traffic(machine_id, attack)
                if threat:
                    threats.append(threat)
            else:
                del self._active_attacks[machine_id]

        # Update threat level
        if any(t["severity"] == "critical" for t in threats):
            self._threat_level = "critical"
        elif any(t["severity"] == "high" for t in threats):
            self._threat_level = "high"
        elif threats:
            self._threat_level = "medium"
        else:
            self._threat_level = "low"

        return {
            "threats": threats,
            "network_telemetry": network_telemetry,
            "threat_level": self._threat_level,
            "isolated_machines": list(self._isolated_machines),
        }

    def auto_respond(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automated cyber defense response to a detected threat.
        No human intervention required.
        """
        threat_type = threat.get("threat_type", "")
        severity = threat.get("severity", "low")
        source_ip = threat.get("source_ip", "0.0.0.0")
        target_machine = threat.get("target_machine", "network")

        actions_taken = []

        # Block source IP
        if source_ip and source_ip != "0.0.0.0":
            actions_taken.append({
                "action": "block_ip",
                "target": source_ip,
                "description": f"Blocked suspicious IP {source_ip} at network firewall",
            })

        # Isolate machine for critical threats
        if severity == "critical" and target_machine != "network":
            self._isolated_machines.add(target_machine)
            actions_taken.append({
                "action": "isolate_machine",
                "target": target_machine,
                "description": f"Machine {target_machine} isolated from OT network",
            })

        # Disable unsafe commands for PLC attacks
        if threat_type in (CyberThreatType.COMMAND_INJECTION, CyberThreatType.PLC_OVERRIDE):
            actions_taken.append({
                "action": "disable_unsafe_commands",
                "target": f"PLC_{target_machine}",
                "description": f"Unsafe command channel disabled on PLC_{target_machine}",
            })

        # Trigger system alert
        actions_taken.append({
            "action": "trigger_alert",
            "target": "security_operations",
            "description": f"Security alert dispatched: {threat.get('description', 'threat detected')}",
        })

        # Self-healing safety procedure
        if severity == "critical":
            actions_taken.append({
                "action": "activate_self_healing_safety",
                "target": target_machine,
                "description": "Self-healing safety mode activated to maintain safe operating state",
            })

        response = {
            "response_id": f"RESP_{datetime.utcnow().strftime('%H%M%S%f')[:12]}",
            "threat_id": threat.get("threat_id"),
            "threat_type": threat_type,
            "severity": severity,
            "actions_taken": actions_taken,
            "response_time_ms": round(random.uniform(45, 180), 1),
            "automated": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._response_log.append(response)
        return response

    def simulate_attack(self, attack_type: str, target_machine: Optional[str],
                         intensity: float, simulation) -> Dict[str, Any]:
        """
        Inject a simulated cyber attack for demonstration purposes.
        """
        if not target_machine:
            target_machine = random.choice(["M1", "M2", "M3", "M4", "M5"])

        attack_record = {
            "attack_type": attack_type,
            "target": target_machine,
            "intensity": intensity,
            "ticks_remaining": int(10 * intensity),
        }
        self._active_attacks[target_machine] = attack_record

        # Apply physical effect for PLC override attacks
        if attack_type == CyberThreatType.PLC_OVERRIDE:
            machine = simulation.get_machine_state(target_machine)
            if machine:
                machine.is_under_cyber_attack = True
                machine.set_fault("speed", 0.5 + intensity * 0.3)
                machine.set_fault("load", 1.2 + intensity * 0.3)

        return {
            "status": "attack_simulated",
            "attack_type": attack_type,
            "target_machine": target_machine,
            "intensity": intensity,
            "estimated_duration_ticks": attack_record["ticks_remaining"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "threat_level": self._threat_level,
            "active_attacks": len(self._active_attacks),
            "isolated_machines": list(self._isolated_machines),
            "blocked_ips": self._ids.get_blocked_ips(),
            "total_threats_detected": len(self._ids._threat_history),
            "total_responses": len(self._response_log),
            "network_status": "compromised" if self._active_attacks else "secure",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_threat_history(self, limit: int = 20) -> List[Dict]:
        return self._ids.get_threat_history(limit)
