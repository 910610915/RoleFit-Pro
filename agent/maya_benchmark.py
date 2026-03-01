# Maya Benchmark Script
# Runs Maya benchmark tests and reports results to server

import os
import sys
import json
import time
import logging
import subprocess
import requests
import psutil
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
SERVER_URL = "http://localhost:8000"
DEVICE_ID = None

# Maya paths (adjust for your installation)
MAYA_PATHS = [
    r"C:\Program Files\Autodesk\Maya2024\bin\maya.exe",
    r"C:\Program Files\Autodesk\Maya2023\bin\maya.exe",
    r"C:\Program Files\Autodesk\Maya2022\bin\maya.exe",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("maya_benchmark.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MayaBenchmark:
    """Run Maya benchmark tests"""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.maya_path = self._find_maya()

    def _find_maya(self) -> Optional[str]:
        """Find Maya executable"""
        for path in MAYA_PATHS:
            if os.path.exists(path):
                logger.info(f"Found Maya: {path}")
                return path
        return None

    def _get_maya_process(self):
        """Get Maya process if running"""
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if "maya" in proc.info["name"].lower():
                    return proc
            except:
                pass
        return None

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics during benchmark"""
        maya = self._get_maya_process()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": 0,
            "memory_mb": 0,
            "gpu_percent": self._get_gpu_usage(),
        }

        if maya:
            try:
                metrics["cpu_percent"] = maya.cpu_percent(interval=0.5)
                metrics["memory_mb"] = maya.memory_info().rss / (1024 * 1024)
            except:
                pass

        metrics["system_cpu"] = psutil.cpu_percent(interval=0.1)
        metrics["system_memory"] = psutil.virtual_memory().percent

        return metrics

    def _get_gpu_usage(self) -> Optional[float]:
        """Get GPU usage"""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return float(result.stdout.strip().split("\n")[0])
        except:
            pass
        return None

    def run_viewport_benchmark(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Run viewport performance benchmark"""
        if not self.maya_path:
            return {"status": "failed", "error": "Maya not found"}

        logger.info(f"Starting Maya viewport benchmark for {duration_seconds}s")

        # Launch Maya with a Python script to test viewport
        script = f"""
import maya.cmds as cmds
import time

# Create test scene
cmds.polyCube(w=10, h=10, d=10)
cmds.polySphere(r=5)

# Rotate viewport for stress test
for i in range({duration_seconds}):
    cmds.rotate(i * 2, i * 3, 0, 'persp', r=True)
    time.sleep(1)

print("Benchmark complete")
"""

        try:
            start_time = datetime.utcnow()

            # Start Maya in background
            proc = subprocess.Popen(
                [self.maya_path, "-c", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Monitor for duration
            metrics_history = []
            for _ in range(duration_seconds // 2):
                if proc.poll() is not None:
                    break
                metrics_history.append(self._collect_metrics())
                time.sleep(2)

            # Terminate Maya
            proc.terminate()
            proc.wait(timeout=10)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return self._analyze_results(duration, metrics_history)

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _analyze_results(
        self, duration: float, metrics_history: list
    ) -> Dict[str, Any]:
        """Analyze collected metrics"""
        if not metrics_history:
            return {"status": "failed", "error": "No metrics collected"}

        cpu_values = [m["cpu_percent"] for m in metrics_history if m.get("cpu_percent")]
        gpu_values = [m["gpu_percent"] for m in metrics_history if m.get("gpu_percent")]
        memory_values = [m["memory_mb"] for m in metrics_history if m.get("memory_mb")]

        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        avg_gpu = sum(gpu_values) / len(gpu_values) if gpu_values else 0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0

        # Determine bottleneck
        if avg_gpu > 80:
            bottleneck = "GPU"
        elif avg_cpu > 80:
            bottleneck = "CPU"
        elif avg_memory > 8000:
            bottleneck = "MEMORY"
        else:
            bottleneck = "NONE"

        return {
            "status": "success",
            "duration_seconds": duration,
            "software_code": "maya",
            "benchmark_type": "viewport",
            "score": round((avg_gpu + avg_cpu) / 2, 1),
            "score_gpu": round(avg_gpu, 1),
            "score_cpu": round(avg_cpu, 1),
            "avg_cpu_percent": round(avg_cpu, 1),
            "avg_gpu_percent": round(avg_gpu, 1),
            "avg_memory_mb": round(avg_memory, 1),
            "bottleneck_type": bottleneck,
        }

    def submit_results(self, results: Dict[str, Any]) -> bool:
        """Submit results to server"""
        try:
            url = f"{SERVER_URL}/api/performance/benchmarks"
            data = {
                "device_id": self.device_id,
                "software_code": results.get("software_code", "maya"),
                "benchmark_type": results.get("benchmark_type", "viewport"),
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": results.get("duration_seconds"),
                "score": results.get("score"),
                "score_cpu": results.get("score_cpu"),
                "score_gpu": results.get("score_gpu"),
                "avg_cpu_percent": results.get("avg_cpu_percent"),
                "avg_gpu_percent": results.get("avg_gpu_percent"),
                "avg_memory_mb": results.get("avg_memory_mb"),
                "status": results.get("status"),
                "bottleneck_type": results.get("bottleneck_type"),
            }

            response = requests.post(url, json=data, timeout=30)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to submit results: {e}")
            return False


def load_device_id() -> Optional[str]:
    """Load device ID from file"""
    try:
        if os.path.exists("device_id.txt"):
            with open("device_id.txt", "r") as f:
                return f.read().strip()
    except:
        pass
    return None


def main():
    global DEVICE_ID

    logger.info("=== Maya Benchmark Tool ===")

    DEVICE_ID = load_device_id()
    if not DEVICE_ID:
        logger.error("Device ID not found")
        return

    benchmark = MayaBenchmark(DEVICE_ID)
    results = benchmark.run_viewport_benchmark(60)

    benchmark.submit_results(results)

    print("\n=== Benchmark Results ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
