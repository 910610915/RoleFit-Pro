# Hardware Performance Monitor Agent
# Collects real-time hardware metrics and reports to server

import os
import sys
import json
import time
import logging
import platform
import requests
import psutil
import wmi
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configuration
SERVER_URL = "http://localhost:8000"
DEVICE_ID = None  # Will be loaded from file or registered
METRICS_INTERVAL = 5  # seconds between metric collections
BATCH_SIZE = 10  # send metrics in batches

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Collect and report real-time performance metrics"""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.wmi = wmi.WMI()
        self.metrics_buffer = []
        self.running = True

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        try:
            metrics = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_temperature": self._get_cpu_temperature(),
                "cpu_frequency": psutil.cpu_freq().current
                if psutil.cpu_freq()
                else None,
                "gpu_percent": self._get_gpu_usage(),
                "gpu_temperature": self._get_gpu_temperature(),
                "gpu_memory_used": self._get_gpu_memory_used(),
                "gpu_memory_total": self._get_gpu_memory_total(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used": psutil.virtual_memory().used / (1024 * 1024),  # MB
                "memory_available": psutil.virtual_memory().available
                / (1024 * 1024),  # MB
                "disk_io": self._get_disk_io(),
                "network_io": self._get_network_io(),
                "process_count": len(psutil.pids()),
                "top_processes": self._get_top_processes(),
            }
            return metrics
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}

    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature"""
        try:
            # Try WMI first
            for temp in self.wmi.Win32_TemperatureProbe():
                if temp.CurrentReading:
                    return round(temp.CurrentReading / 10.0 - 273.15, 1)
        except:
            pass
        return None

    def _get_gpu_usage(self) -> Optional[float]:
        """Get GPU usage percentage"""
        try:
            import subprocess

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

    def _get_gpu_temperature(self) -> Optional[float]:
        """Get GPU temperature"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
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

    def _get_gpu_memory_used(self) -> Optional[float]:
        """Get GPU memory used in MB"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used",
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

    def _get_gpu_memory_total(self) -> Optional[float]:
        """Get GPU total memory in MB"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
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

    def _get_disk_io(self) -> Dict[str, float]:
        """Get disk I/O statistics"""
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                return {
                    "read_mbps": disk_io.read_bytes / (1024 * 1024),  # MB
                    "write_mbps": disk_io.write_bytes / (1024 * 1024),  # MB
                }
        except:
            pass
        return {"read_mbps": 0, "write_mbps": 0}

    def _get_network_io(self) -> Dict[str, float]:
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                return {
                    "sent_mbps": net_io.bytes_sent / (1024 * 1024),  # MB
                    "recv_mbps": net_io.bytes_recv / (1024 * 1024),  # MB
                }
        except:
            pass
        return {"sent_mbps": 0, "recv_mbps": 0}

    def _get_top_processes(self) -> List[Dict[str, Any]]:
        """Get top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
                try:
                    pinfo = proc.info
                    if pinfo["cpu_percent"] and pinfo["cpu_percent"] > 0:
                        processes.append(
                            {
                                "name": pinfo["name"][:50],
                                "cpu": round(pinfo["cpu_percent"], 1),
                                "memory": round(
                                    pinfo["memory_info"].rss / (1024 * 1024), 1
                                )
                                if pinfo.get("memory_info")
                                else 0,
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Sort by CPU and return top 10
            processes.sort(key=lambda x: x["cpu"], reverse=True)
            return processes[:10]
        except:
            return []

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics to server"""
        try:
            url = f"{SERVER_URL}/api/performance/metrics"
            response = requests.post(url, json=metrics, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")
            return False

    def send_metrics_batch(self, metrics_list: List[Dict[str, Any]]) -> bool:
        """Send batch metrics to server"""
        try:
            url = f"{SERVER_URL}/api/performance/metrics/batch"
            response = requests.post(
                url,
                json={"device_id": self.device_id, "metrics": metrics_list},
                timeout=30,
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send batch metrics: {e}")
            return False

    def run(self):
        """Main monitoring loop"""
        logger.info(f"Starting performance monitor for device: {self.device_id}")

        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                if metrics:
                    self.metrics_buffer.append(metrics)
                    logger.debug(
                        f"Collected metrics: CPU={metrics.get('cpu_percent')}%, GPU={metrics.get('gpu_percent')}%, Memory={metrics.get('memory_percent')}%"
                    )

                # Send batch when buffer is full
                if len(self.metrics_buffer) >= BATCH_SIZE:
                    if self.send_metrics_batch(self.metrics_buffer):
                        logger.info(f"Sent batch of {len(self.metrics_buffer)} metrics")
                        self.metrics_buffer.clear()
                    else:
                        logger.warning("Failed to send batch, will retry next cycle")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(METRICS_INTERVAL)

        # Send remaining metrics before exit
        if self.metrics_buffer:
            self.send_metrics_batch(self.metrics_buffer)

        logger.info("Performance monitor stopped")

    def stop(self):
        """Stop the monitoring"""
        self.running = False


def load_device_id() -> Optional[str]:
    """Load device ID from file"""
    try:
        if os.path.exists("device_id.txt"):
            with open("device_id.txt", "r") as f:
                return f.read().strip()
    except:
        pass
    return None


def register_device() -> Optional[str]:
    """Register device with server and get device ID"""
    try:
        # Get basic hardware info
        import platform
        import uuid

        # Get MAC address
        mac = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 8 * 6, 8)
            ][::-1]
        )

        register_data = {
            "device_name": platform.node(),
            "hostname": platform.node(),
            "mac_address": mac,
            "ip_address": requests.get("https://api.ipify.org", timeout=5).text,
        }

        url = f"{SERVER_URL}/api/devices/agent/register"
        response = requests.post(url, json=register_data, timeout=10)

        if response.status_code in [200, 201]:
            data = response.json()
            device_id = data.get("id")

            # Save device ID
            with open("device_id.txt", "w") as f:
                f.write(device_id)

            logger.info(f"Registered device: {device_id}")
            return device_id
    except Exception as e:
        logger.error(f"Failed to register device: {e}")

    return None


def main():
    """Main entry point"""
    global DEVICE_ID

    logger.info("=== Hardware Performance Monitor ===")

    # Load or register device
    DEVICE_ID = load_device_id()
    if not DEVICE_ID:
        logger.info("Device not registered, registering...")
        DEVICE_ID = register_device()

    if not DEVICE_ID:
        logger.error("Cannot proceed without device ID")
        return

    # Start monitoring
    monitor = PerformanceMonitor(DEVICE_ID)

    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Received stop signal")
        monitor.stop()


if __name__ == "__main__":
    main()
