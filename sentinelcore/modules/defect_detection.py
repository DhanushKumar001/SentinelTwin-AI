"""
SentinelTwin AI — Defect Detection Vision AI Module
Simulates computer vision defect detection using YOLOv8, Swin Transformer, and Mask R-CNN.
Monitors the Quality Inspection Machine (M3) for product defects.
"""

import random
import math
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sentinelcore.config import DEFECT_TYPES, MACHINE_MAP, MachineStatus, AlertLevel


class YOLOv8Detector:
    """
    Simulates YOLOv8 real-time object detection for defect bounding boxes.
    Fast detection with bounding box output.
    """

    def __init__(self):
        self.model_version = "YOLOv8-industrial-v2.3"
        self.inference_time_ms = 12.0

    def detect(self, image_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run YOLOv8 detection on a simulated product image.
        Returns detection results with bounding box coordinates.
        """
        # Detection confidence influenced by machine health and product complexity
        machine_health = image_context.get("machine_health", 100.0)
        anomaly_score = image_context.get("anomaly_score", 0.0)
        production_rate = image_context.get("production_rate", 90.0)

        # Base defect probability: poor machine health → more defects
        base_prob = 0.02 + (1.0 - machine_health / 100.0) * 0.30 + anomaly_score * 0.25

        has_defect = random.random() < min(0.95, base_prob)

        if not has_defect:
            return {
                "model": "YOLOv8",
                "defect_detected": False,
                "confidence": round(random.uniform(0.02, 0.15), 3),
                "inference_time_ms": self.inference_time_ms + random.uniform(-2, 2),
            }

        defect_type = random.choice(DEFECT_TYPES)
        confidence = random.uniform(0.72, 0.98)

        # Bounding box (normalized [0,1] coordinates: x_center, y_center, width, height)
        x_c = round(random.uniform(0.2, 0.8), 3)
        y_c = round(random.uniform(0.2, 0.8), 3)
        w = round(random.uniform(0.05, 0.35), 3)
        h = round(random.uniform(0.05, 0.35), 3)

        return {
            "model": "YOLOv8",
            "defect_detected": True,
            "defect_type": defect_type,
            "confidence": round(confidence, 3),
            "bounding_box": {
                "x_center": x_c,
                "y_center": y_c,
                "width": w,
                "height": h,
                "x1": round(x_c - w / 2, 3),
                "y1": round(y_c - h / 2, 3),
                "x2": round(x_c + w / 2, 3),
                "y2": round(y_c + h / 2, 3),
            },
            "inference_time_ms": round(self.inference_time_ms + random.uniform(-2, 2), 1),
        }


class SwinTransformerDetector:
    """
    Simulates Swin Transformer for hierarchical feature extraction and defect classification.
    Higher accuracy than YOLO, slower inference.
    """

    def __init__(self):
        self.model_version = "SwinTransformer-Industrial-Large"
        self.inference_time_ms = 45.0

    def classify(self, yolo_result: Dict[str, Any],
                 image_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify defect type and severity using Swin Transformer.
        Works on top of YOLO's detected region.
        """
        if not yolo_result.get("defect_detected"):
            return {
                "model": "SwinTransformer",
                "classification": "no_defect",
                "severity": "none",
                "confidence": round(random.uniform(0.92, 0.99), 3),
                "inference_time_ms": self.inference_time_ms,
            }

        defect_type = yolo_result.get("defect_type", "surface_defect")

        severity_weights = {
            "structural_damage": ("critical", 0.85),
            "surface_defect": ("medium", 0.78),
            "misalignment": ("high", 0.82),
            "missing_component": ("critical", 0.91),
            "dimensional_error": ("high", 0.79),
            "coating_defect": ("low", 0.88),
            "assembly_error": ("high", 0.84),
        }
        severity, base_conf = severity_weights.get(defect_type, ("medium", 0.75))

        # Agreement boost: if Swin agrees with YOLO, confidence goes up
        yolo_conf = yolo_result.get("confidence", 0.7)
        final_conf = base_conf * 0.7 + yolo_conf * 0.3 + random.uniform(-0.03, 0.03)

        return {
            "model": "SwinTransformer",
            "classification": defect_type,
            "severity": severity,
            "confidence": round(min(0.99, max(0.55, final_conf)), 3),
            "feature_map_highlight": self._generate_attention_map(),
            "inference_time_ms": round(self.inference_time_ms + random.uniform(-5, 10), 1),
        }

    def _generate_attention_map(self) -> List[List[float]]:
        """Generate a simulated 4x4 attention heatmap (normalized)."""
        grid = []
        for _ in range(4):
            row = [round(random.uniform(0.1, 1.0), 2) for _ in range(4)]
            grid.append(row)
        # Boost one cell to simulate focused attention
        r, c = random.randint(0, 3), random.randint(0, 3)
        grid[r][c] = round(random.uniform(0.85, 1.0), 2)
        return grid


class MaskRCNNSegmentor:
    """
    Simulates Mask R-CNN for instance segmentation of defective regions.
    Produces pixel-level defect masks.
    """

    def __init__(self):
        self.model_version = "MaskRCNN-ResNet101-FPN"
        self.inference_time_ms = 120.0

    def segment(self, yolo_result: Dict[str, Any],
                swin_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate segmentation mask for detected defect.
        """
        if not yolo_result.get("defect_detected"):
            return {
                "model": "MaskRCNN",
                "segmentation_available": False,
                "mask_pixel_count": 0,
                "defect_area_pct": 0.0,
            }

        bbox = yolo_result.get("bounding_box", {})
        width = bbox.get("width", 0.1)
        height = bbox.get("height", 0.1)

        # Segmentation mask covers ~70-90% of bounding box area
        mask_coverage = random.uniform(0.70, 0.92)
        defect_area_pct = width * height * mask_coverage * 100.0

        # Simulate polygon mask points (simplified contour)
        x1 = bbox.get("x1", 0.3)
        y1 = bbox.get("y1", 0.3)
        x2 = bbox.get("x2", 0.6)
        y2 = bbox.get("y2", 0.6)

        polygon = [
            [round(x1 + random.uniform(-0.01, 0.01), 3), round(y1 + random.uniform(-0.01, 0.01), 3)],
            [round(x2 + random.uniform(-0.01, 0.01), 3), round(y1 + random.uniform(-0.01, 0.01), 3)],
            [round(x2 + random.uniform(-0.01, 0.01), 3), round(y2 + random.uniform(-0.01, 0.01), 3)],
            [round(x1 + random.uniform(-0.01, 0.01), 3), round(y2 + random.uniform(-0.01, 0.01), 3)],
        ]

        return {
            "model": "MaskRCNN",
            "segmentation_available": True,
            "mask_pixel_count": int(defect_area_pct * 100),
            "defect_area_pct": round(defect_area_pct, 3),
            "mask_polygon": polygon,
            "mask_coverage_ratio": round(mask_coverage, 3),
            "inference_time_ms": round(self.inference_time_ms + random.uniform(-15, 20), 1),
        }


class DefectDetectionAI:
    """
    Master Defect Detection Vision AI engine.
    Orchestrates YOLOv8 → Swin Transformer → Mask R-CNN pipeline.
    Monitors the Quality Inspection Machine (M3).
    """

    def __init__(self):
        self._yolo = YOLOv8Detector()
        self._swin = SwinTransformerDetector()
        self._maskrcnn = MaskRCNNSegmentor()

        self._defect_history: deque = deque(maxlen=100)
        self._total_products_inspected: int = 0
        self._total_defects_found: int = 0
        self._consecutive_defects: int = 0

        # Simulated camera frame counter
        self._frame_id: int = 0

    def detect(self, factory_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full defect detection pipeline on the latest product image
        from the Quality Inspection Machine (M3).
        """
        self._frame_id += 1
        self._total_products_inspected += 1

        m3_data = factory_state.get("machines", {}).get("M3", {})
        machine_health = m3_data.get("health_score", 100.0)
        sensors = m3_data.get("sensors", {})
        status = m3_data.get("status", MachineStatus.NORMAL)

        # Also consider upstream M2 assembly quality
        m2_data = factory_state.get("machines", {}).get("M2", {})
        m2_health = m2_data.get("health_score", 100.0) if m2_data else 100.0

        image_context = {
            "machine_health": min(machine_health, m2_health),
            "anomaly_score": 0.0 if status == MachineStatus.NORMAL else 0.4,
            "production_rate": sensors.get("production_rate", 90.0),
            "frame_id": self._frame_id,
        }

        # Adjust anomaly score for critical states
        if status in (MachineStatus.CRITICAL, MachineStatus.FAILURE):
            image_context["anomaly_score"] = 0.7

        # Stage 1: YOLOv8 detection
        yolo_result = self._yolo.detect(image_context)

        # Stage 2: Swin Transformer classification
        swin_result = self._swin.classify(yolo_result, image_context)

        # Stage 3: Mask R-CNN segmentation (only if defect detected)
        mask_result = self._maskrcnn.segment(yolo_result, swin_result)

        # Ensemble decision
        defect_found = yolo_result.get("defect_detected", False)
        if defect_found:
            self._total_defects_found += 1
            self._consecutive_defects += 1
        else:
            self._consecutive_defects = 0

        defect_rate = (self._total_defects_found / self._total_products_inspected * 100
                       if self._total_products_inspected > 0 else 0.0)

        result = {
            "frame_id": self._frame_id,
            "machine_id": "M3",
            "machine_name": "Quality Inspection Machine",
            "defect_found": defect_found,
            "defect_type": swin_result.get("classification") if defect_found else None,
            "severity": swin_result.get("severity", "none"),
            "confidence": round(
                (yolo_result.get("confidence", 0) + swin_result.get("confidence", 0)) / 2.0, 3
            ) if defect_found else 0.0,
            "bounding_box": yolo_result.get("bounding_box") if defect_found else None,
            "segmentation": mask_result if defect_found else None,
            "attention_map": swin_result.get("feature_map_highlight") if defect_found else None,
            "model_pipeline": {
                "yolov8": yolo_result,
                "swin_transformer": swin_result,
                "mask_rcnn": mask_result,
            },
            "inspection_stats": {
                "total_inspected": self._total_products_inspected,
                "total_defects": self._total_defects_found,
                "defect_rate_pct": round(defect_rate, 2),
                "consecutive_defects": self._consecutive_defects,
            },
            "total_inference_time_ms": round(
                yolo_result.get("inference_time_ms", 0)
                + swin_result.get("inference_time_ms", 0)
                + mask_result.get("inference_time_ms", 0), 1
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if defect_found:
            self._defect_history.append(result)

        return result

    def get_defect_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent defect detection history."""
        history = list(self._defect_history)
        return history[-limit:]

    def get_quality_stats(self) -> Dict[str, Any]:
        """Return overall quality inspection statistics."""
        defect_rate = (self._total_defects_found / max(1, self._total_products_inspected) * 100)
        return {
            "total_inspected": self._total_products_inspected,
            "total_defects": self._total_defects_found,
            "defect_rate_pct": round(defect_rate, 2),
            "quality_rate_pct": round(100.0 - defect_rate, 2),
            "consecutive_defects": self._consecutive_defects,
        }
