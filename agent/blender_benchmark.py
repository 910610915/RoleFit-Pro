# Blender Benchmark Script
# Runs Blender benchmark tests and reports results to server

import os
import sys
import json
import time
import logging
import subprocess
import requests
import psutil
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configuration
SERVER_URL = "http://localhost:8000"
DEVICE_ID = None  # Will be loaded from file
BLENDER_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
    r"C:\Program Files\Blender\blender.exe",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("blender_benchmark.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BlenderBenchmark:
    """Run Blender benchmark tests"""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.blender_path = self._find_blender()
        self.process = None
        self.metrics_history = []
        self.start_time = None

    def _find_blender(self) -> Optional[str]:
        """Find Blender executable"""
        for path in BLENDER_PATHS:
            if os.path.exists(path):
                logger.info(f"Found Blender: {path}")
                return path

        # Try to find via registry
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\BlenderFoundation\Blender",
                0,
                winreg.KEY_READ,
            )
            install_path = winreg.QueryValueEx(key, "InstallPath")[0]
            blender_path = os.path.join(install_path, "blender.exe")
            if os.path.exists(blender_path):
                return blender_path
        except:
            pass

        return None

    def _get_blender_process(self) -> Optional[psutil.Process]:
        """Get Blender process if running"""
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if "blender" in proc.info["name"].lower():
                    return proc
            except:
                pass
        return None

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics while Blender is running"""
        blender_proc = self._get_blender_process()

        if not blender_proc:
            return {}

        try:
            # Get CPU and memory for Blender
            cpu_percent = blender_proc.cpu_percent(interval=0.5)
            mem_info = blender_proc.memory_info()
            memory_mb = mem_info.rss / (1024 * 1024)

            # Get GPU usage
            gpu_percent = self._get_gpu_usage()

            # Get system-wide metrics
            sys_cpu = psutil.cpu_percent(interval=0.1)
            sys_memory = psutil.virtual_memory().percent

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "gpu_percent": gpu_percent,
                "system_cpu_percent": sys_cpu,
                "system_memory_percent": sys_memory,
            }
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}

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

    def _monitor_loop(self):
        """Monitor Blender while it's running"""
        logger.info("Starting benchmark monitoring loop")

        while True:
            # Check if Blender is still running
            blender = self._get_blender_process()
            if not blender:
                logger.info("Blender process ended")
                break

            # Collect metrics
            metrics = self._collect_metrics()
            if metrics:
                self.metrics_history.append(metrics)

            time.sleep(2)

    def run_benchmark(
        self, scene_file: Optional[str] = None, samples: int = 128
    ) -> Dict[str, Any]:
        """
        Run Blender benchmark

        Args:
            scene_file: Path to .blend file (optional, will use default scene)
            samples: Number of render samples

        Returns:
            Benchmark results
        """
        if not self.blender_path:
            return {"status": "failed", "error": "Blender not found"}

        logger.info(f"Starting Blender benchmark with {samples} samples")

        # Prepare render command
        cmd = [
            self.blender_path,
            "--background",
            "--engine",
            "CYCLES",
            "--threads",
            str(psutil.cpu_count()),
        ]

        # If no scene file, create a default benchmark scene
        if not scene_file:
            scene_file = self._create_default_scene()
            if not scene_file:
                return {"status": "failed", "error": "Failed to create test scene"}

        cmd.extend(
            [
                "--python-expr",
                f"""
import bpy
bpy.ops.wm.open(filepath='{scene_file}')
bpy.context.scene.cycles.samples = {samples}
bpy.ops.render.render(animation=False, write_still=False)
import sys
sys.exit(0)
""",
            ]
        )

        try:
            # Start Blender
            self.start_time = datetime.utcnow()

            # Monitor in a separate thread
            import threading

            monitor_thread = threading.Thread(target=self._monitor_loop)
            monitor_thread.start()

            # Run Blender
            logger.info(f"Running: {' '.join(cmd[:5])}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            # Wait for monitor to finish
            monitor_thread.join(timeout=5)

            # Calculate results
            end_time = datetime.utcnow()
            duration = (end_time - self.start_time).total_seconds()

            # Analyze metrics
            return self._analyze_results(duration)

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Benchmark timed out after 10 minutes",
            }
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _create_default_scene(self) -> Optional[str]:
        """Create a default benchmark scene"""
        script = r"""
import bpy
import math

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Create cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object

# Add material
mat = bpy.data.materials.new(name="CubeMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1)
bsdf.inputs["Metallic"].default_value = 0.5
bsdf.inputs["Roughness"].default_value = 0.3
cube.data.materials.append(mat)

# Add light
bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 5

# Add camera
bpy.ops.object.camera_add(location=(7, -7, 5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(60), 0, math.radians(45))
bpy.context.scene.camera = cam

# Add floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object

# Set output
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 128
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

# Save
bpy.ops.wm.save_as_mainfile(filepath="benchmark_scene.blend")
"""

        try:
            result = subprocess.run(
                [self.blender_path, "--background", "--python-expr", script],
                capture_output=True,
                text=True,
                timeout=60,
            )

            scene_path = os.path.join(os.getcwd(), "benchmark_scene.blend")
            if os.path.exists(scene_path):
                return scene_path
        except Exception as e:
            logger.error(f"Failed to create scene: {e}")

        return None

    def _analyze_results(self, duration: float) -> Dict[str, Any]:
        """Analyze collected metrics and generate results"""
        if not self.metrics_history:
            return {"status": "failed", "error": "No metrics collected"}

        # Calculate averages and peaks
        cpu_values = [m["cpu_percent"] for m in self.metrics_history]
        gpu_values = [
            m["gpu_percent"] for m in self.metrics_history if m.get("gpu_percent")
        ]
        memory_values = [m["memory_mb"] for m in self.metrics_history]

        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        avg_gpu = sum(gpu_values) / len(gpu_values) if gpu_values else 0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0

        peak_cpu = max(cpu_values) if cpu_values else 0
        peak_gpu = max(gpu_values) if gpu_values else 0
        peak_memory = max(memory_values) if memory_values else 0

        # Estimate score (simplified)
        score_gpu = avg_gpu * 10 if avg_gpu > 0 else 50
        score_cpu = (100 - avg_cpu) * 0.5
        score = (score_gpu + score_cpu) / 2

        # Determine bottleneck
        if avg_gpu > 80:
            bottleneck = "GPU"
        elif avg_cpu > 80:
            bottleneck = "CPU"
        elif avg_memory > 85:
            bottleneck = "MEMORY"
        else:
            bottleneck = "NONE"

        results = {
            "status": "success",
            "duration_seconds": duration,
            "score": round(score, 1),
            "score_cpu": round(score_cpu, 1),
            "score_gpu": round(score_gpu, 1),
            "avg_cpu_percent": round(avg_cpu, 1),
            "avg_gpu_percent": round(avg_gpu, 1),
            "avg_memory_mb": round(avg_memory, 1),
            "peak_cpu_percent": round(peak_cpu, 1),
            "peak_gpu_percent": round(peak_gpu, 1),
            "peak_memory_mb": round(peak_memory, 1),
            "bottleneck_type": bottleneck,
            "samples_collected": len(self.metrics_history),
        }

        logger.info(
            f"Benchmark completed: score={results['score']}, bottleneck={bottleneck}"
        )

        return results

    def submit_results(self, results: Dict[str, Any]) -> bool:
        """Submit benchmark results to server"""
        try:
            url = f"{SERVER_URL}/api/performance/benchmarks"

            data = {
                "device_id": self.device_id,
                "software_code": "blender",
                "benchmark_type": "render",
                "test_scene": "default",
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
                "peak_memory_mb": results.get("peak_memory_mb"),
                "status": results.get("status"),
                "bottleneck_type": results.get("bottleneck_type"),
                "error_message": results.get("error"),
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
    """Main entry point"""
    global DEVICE_ID

    logger.info("=== Blender Benchmark Tool ===")

    # Load device ID
    DEVICE_ID = load_device_id()
    if not DEVICE_ID:
        logger.error("Device ID not found. Run hardware_agent.py first.")
        return

    # Parse arguments
    samples = 128
    scene_file = None

    if len(sys.argv) > 1:
        try:
            samples = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) > 2:
        scene_file = sys.argv[2]

    # Run benchmark
    benchmark = BlenderBenchmark(DEVICE_ID)
    results = benchmark.run_benchmark(scene_file, samples)

    # Submit results
    if benchmark.submit_results(results):
        logger.info("Results submitted successfully")
    else:
        logger.warning("Failed to submit results")

    # Print results
    print("\n=== Benchmark Results ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
