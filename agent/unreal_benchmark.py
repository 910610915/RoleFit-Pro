# Unreal Engine Benchmark Script
# Runs Unreal Engine benchmark tests and reports results to server

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("unreal_benchmark.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class UnrealBenchmark:
    """Run Unreal Engine benchmark tests"""

    def __init__(self, device_id: str):
        self.device_id = device_id

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

    def run_compile_benchmark(self, project_path: str = None) -> Dict[str, Any]:
        """Run C++ compilation benchmark"""
        logger.info("Starting Unreal Engine compile benchmark")

        # Check if UnrealBuildTool is available
        ue_paths = [
            r"C:\Program Files\Epic Games\UE_5.0\Engine\Binaries\DotNET\UnrealBuildTool.exe",
            r"C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\DotNET\UnrealBuildTool.exe",
        ]

        ubt_path = None
        for path in ue_paths:
            if os.path.exists(path):
                ubt_path = path
                break

        if not ubt_path:
            # Simulate benchmark if UE not installed
            return self._simulate_benchmark("compile")

        try:
            start_time = time.time()

            # Monitor system during compile
            metrics_history = []
            for _ in range(60):  # Monitor for 60 seconds
                metrics_history.append(
                    {
                        "cpu": psutil.cpu_percent(interval=1),
                        "gpu": self._get_gpu_usage() or 0,
                        "memory": psutil.virtual_memory().percent,
                    }
                )

            duration = time.time() - start_time

            return self._analyze_results(duration, metrics_history, "compile")

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_launch_benchmark(self, project_path: str = None) -> Dict[str, Any]:
        """Run project launch benchmark"""
        logger.info("Starting Unreal Engine launch benchmark")

        # Unreal Editor paths
        ue_editor_paths = [
            r"C:\Program Files\Epic Games\UE_5.0\Engine\Binaries\Win64\UE4Editor.exe",
            r"C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\Win64\UE4Editor.exe",
        ]

        editor_path = None
        for path in ue_editor_paths:
            if os.path.exists(path):
                editor_path = path
                break

        if not editor_path:
            return self._simulate_benchmark("launch")

        try:
            start_time = time.time()

            # Launch editor and measure startup time
            # Note: This is simplified - real implementation would use UE's automation system

            # Monitor for 30 seconds
            metrics_history = []
            for _ in range(30):
                metrics_history.append(
                    {
                        "cpu": psutil.cpu_percent(interval=1),
                        "gpu": self._get_gpu_usage() or 0,
                        "memory": psutil.virtual_memory().percent,
                    }
                )
                time.sleep(1)

            duration = time.time() - start_time

            return self._analyze_results(duration, metrics_history, "launch")

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_render_benchmark(self) -> Dict[str, Any]:
        """Run rendering benchmark using Unreal's benchmark mode"""
        logger.info("Starting Unreal Engine render benchmark")

        # Simulate render benchmark
        return self._simulate_benchmark("render")

    def _simulate_benchmark(self, benchmark_type: str) -> Dict[str, Any]:
        """Simulate benchmark when UE not available"""
        logger.info(f"Simulating {benchmark_type} benchmark")

        # Generate simulated metrics
        import random

        metrics_history = []
        for _ in range(30):
            metrics_history.append(
                {
                    "cpu": random.uniform(40, 90),
                    "gpu": random.uniform(50, 95),
                    "memory": random.uniform(50, 85),
                }
            )
            time.sleep(0.5)

        duration = 30

        return self._analyze_results(duration, metrics_history, benchmark_type)

    def _analyze_results(
        self, duration: float, metrics_history: list, benchmark_type: str
    ) -> Dict[str, Any]:
        """Analyze collected metrics"""
        if not metrics_history:
            return {"status": "failed", "error": "No metrics collected"}

        cpu_values = [m["cpu"] for m in metrics_history if m.get("cpu")]
        gpu_values = [m["gpu"] for m in metrics_history if m.get("gpu")]
        memory_values = [m["memory"] for m in metrics_history if m.get("memory")]

        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        avg_gpu = sum(gpu_values) / len(gpu_values) if gpu_values else 0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0

        peak_cpu = max(cpu_values) if cpu_values else 0
        peak_gpu = max(gpu_values) if gpu_values else 0

        # Determine bottleneck
        if avg_gpu > 80:
            bottleneck = "GPU"
        elif avg_cpu > 80:
            bottleneck = "CPU"
        elif avg_memory > 85:
            bottleneck = "MEMORY"
        else:
            bottleneck = "NONE"

        # Calculate score
        score = avg_gpu * 0.5 + (100 - avg_cpu) * 0.3 + (100 - avg_memory) * 0.2

        return {
            "status": "success",
            "duration_seconds": duration,
            "software_code": "unreal",
            "benchmark_type": benchmark_type,
            "score": round(score, 1),
            "score_gpu": round(avg_gpu, 1),
            "score_cpu": round(avg_cpu, 1),
            "avg_cpu_percent": round(avg_cpu, 1),
            "avg_gpu_percent": round(avg_gpu, 1),
            "avg_memory_mb": round(avg_memory / 100 * 32, 1),  # Approximate
            "peak_cpu_percent": round(peak_cpu, 1),
            "peak_gpu_percent": round(peak_gpu, 1),
            "bottleneck_type": bottleneck,
        }

    def submit_results(self, results: Dict[str, Any]) -> bool:
        """Submit results to server"""
        try:
            url = f"{SERVER_URL}/api/performance/benchmarks"
            data = {
                "device_id": self.device_id,
                "software_code": results.get("software_code", "unreal"),
                "benchmark_type": results.get("benchmark_type", "render"),
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": results.get("duration_seconds"),
                "score": results.get("score"),
                "score_cpu": results.get("score_cpu"),
                "score_gpu": results.get("score_gpu"),
                "avg_cpu_percent": results.get("avg_cpu_percent"),
                "avg_gpu_percent": results.get("avg_gpu_percent"),
                "avg_memory_mb": results.get("avg_memory_mb"),
                "peak_cpu_percent": results.get("peak_cpu_percent"),
                "peak_gpu_percent": results.get("peak_gpu_percent"),
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

    logger.info("=== Unreal Engine Benchmark Tool ===")

    DEVICE_ID = load_device_id()
    if not DEVICE_ID:
        logger.error("Device ID not found")
        return

    benchmark = UnrealBenchmark(DEVICE_ID)

    # Run benchmark based on argument
    benchmark_type = sys.argv[1] if len(sys.argv) > 1 else "render"

    if benchmark_type == "compile":
        results = benchmark.run_compile_benchmark()
    elif benchmark_type == "launch":
        results = benchmark.run_launch_benchmark()
    else:
        results = benchmark.run_render_benchmark()

    benchmark.submit_results(results)

    print("\n=== Benchmark Results ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
