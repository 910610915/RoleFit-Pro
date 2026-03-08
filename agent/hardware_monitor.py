# Hardware Performance Monitor Agent
# Collects real-time hardware metrics and reports to server
# Uses Node.js + systeminformation for accurate data

import os
import sys
import json
import time
import logging
import platform
import requests
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import Node.js hardware wrapper
try:
    from nodejs_hardware import get_realtime_metrics as get_metrics_nodejs

    NODEJS_AVAILABLE = True
except ImportError:
    NODEJS_AVAILABLE = False
    get_metrics_nodejs = None
    print(
        "ERROR: Failed to import Node.js wrapper. Please run: cd nodejs/hardware_info && npm install"
    )
    sys.exit(1)

# Configuration
SERVER_URL = "http://localhost:8000"
DEVICE_ID = None  # Will be loaded from file or registered
METRICS_INTERVAL = 1  # seconds between metric collections
BATCH_SIZE = 1  # send metrics in batches

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
    """Register device with server to get device_id"""
    try:
        import socket

        # Get basic info
        hostname = socket.gethostname()

        # Try to get MAC address
        mac = ""
        try:
            import subprocess

            result = subprocess.run(
                ["getmac", "/v", "/fo", "csv"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(",")
                        if len(parts) >= 3:
                            mac = parts[2].strip().strip('"')
                            if mac and mac != "00-00-00-00-00-00":
                                break
        except:
            pass

        if not mac or mac == "00-00-00-00-00-00":
            mac = "00:00:00:00:00:00"
        else:
            mac = mac.replace("-", ":")

        payload = {
            "device_name": hostname,
            "hostname": hostname,
            "mac_address": mac,
            "ip_address": "127.0.0.1",
            "agent_version": "1.0.2",
        }

        url = f"{SERVER_URL}/api/devices/agent/register"
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code in [200, 201]:
            device_data = response.json()
            device_id = device_data.get("id")
            if device_id:
                # Save device_id
                with open("device_id.txt", "w") as f:
                    f.write(device_id)
                logger.info(f"Device registered: {device_id}")
                return device_id

        logger.error(f"Failed to register: {response.status_code}")
        return None

    except Exception as e:
        logger.error(f"Failed to register device: {e}")
        return None


class PerformanceMonitor:
    """Collect and report real-time performance metrics using Node.js systeminformation"""

    def __init__(self, device_id: str, server_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.device_id = device_id
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.metrics_buffer = []
        self.running = True
        
        # State for rate calculation
        self.last_timestamp = 0
        self.last_disk_read = 0
        self.last_disk_write = 0
        self.last_net_sent = 0
        self.last_net_recv = 0

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics from Node.js"""
        try:
            # Get metrics from Node.js
            metrics = get_metrics_nodejs()
            
            if not metrics:
                logger.warning("No metrics returned from Node.js")
                return {}

            # Calculate rates
            current_time = time.time()
            
            if self.last_timestamp > 0:
                time_diff = current_time - self.last_timestamp
                # Avoid division by zero
                if time_diff < 0.1: time_diff = 0.1
                
                # Disk MB/s
                read_diff = metrics.get("disk_read_bytes", 0) - self.last_disk_read
                write_diff = metrics.get("disk_write_bytes", 0) - self.last_disk_write
                
                # Handle counter reset/overflow
                if read_diff < 0: read_diff = 0
                if write_diff < 0: write_diff = 0
                
                metrics["disk_read_mbps"] = round(read_diff / time_diff / (1024*1024), 2)
                metrics["disk_write_mbps"] = round(write_diff / time_diff / (1024*1024), 2)
                
                # Network MB/s
                sent_diff = metrics.get("network_sent_bytes", 0) - self.last_net_sent
                recv_diff = metrics.get("network_recv_bytes", 0) - self.last_net_recv
                
                if sent_diff < 0: sent_diff = 0
                if recv_diff < 0: recv_diff = 0
                
                metrics["network_sent_mbps"] = round(sent_diff / time_diff / (1024*1024), 2)
                metrics["network_recv_mbps"] = round(recv_diff / time_diff / (1024*1024), 2)
            else:
                # First run - set to 0
                metrics["disk_read_mbps"] = 0
                metrics["disk_write_mbps"] = 0
                metrics["network_sent_mbps"] = 0
                metrics["network_recv_mbps"] = 0
                
            # Update state
            self.last_timestamp = current_time
            self.last_disk_read = metrics.get("disk_read_bytes", 0)
            self.last_disk_write = metrics.get("disk_write_bytes", 0)
            self.last_net_sent = metrics.get("network_sent_bytes", 0)
            self.last_net_recv = metrics.get("network_recv_bytes", 0)

            # Pass through the raw details directly from Node.js
            # These are already per-disk objects: { name: "0 C:", queue_length: 0, ... }
            metrics["disk_io_details"] = metrics.get("disk_io_details", [])

            metrics["device_id"] = self.device_id
            metrics["timestamp"] = datetime.utcnow().isoformat()

            
            # Ensure critical fields exist and are numbers
            metrics['memory_used_mb'] = metrics.get('memory_used_mb') or 0
            metrics['memory_available_mb'] = metrics.get('memory_available_mb') or 0
            
            used = metrics['memory_used_mb']
            avail = metrics['memory_available_mb']
            total = used + avail
            
            if 'memory_percent' not in metrics or metrics['memory_percent'] is None:
                if total > 0:
                    metrics['memory_percent'] = round((used / total) * 100, 1)
                else:
                    metrics['memory_percent'] = 0
            
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}

    def send_metrics_batch(self, metrics_list: List[Dict[str, Any]]) -> bool:
        """Send batch metrics to server"""
        try:
            url = f"{self.server_url}/api/performance/metrics/batch"
            
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
                
            response = requests.post(
                url,
                json={"device_id": self.device_id, "metrics": metrics_list},
                headers=headers,
                timeout=30,
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send batch metrics: {e}")
            return False

    def run(self):
        """Main monitoring loop"""
        logger.info("Starting Hardware Performance Monitor...")
        logger.info(f"Using Node.js + systeminformation for metrics")

        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                if metrics:
                    self.metrics_buffer.append(metrics)

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


def main():
    global DEVICE_ID, SERVER_URL

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
    monitor = PerformanceMonitor(DEVICE_ID, SERVER_URL)

    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Received stop signal")
        monitor.stop()


if __name__ == "__main__":
    main()
