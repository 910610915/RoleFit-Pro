# Hardware Benchmark Agent
# Runs on Windows devices to collect hardware info and report to server
# Now uses Node.js + systeminformation for accurate hardware data

import os
import sys
import json
import time
import socket
import logging
import platform
import uuid
import requests
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class HardwareBenchmarkAgent:
    """Main agent class for hardware benchmark reporting using Node.js systeminformation"""

    # GitHub update configuration
    GITHUB_OWNER = "910610915"
    GITHUB_REPO = "RoleFit-Pro"
    CURRENT_VERSION = "1.0.2"

    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.device_id = None
        self.running = True
        self.heartbeat_interval = 60  # seconds
        self.task_poll_interval = 10  # seconds
        self.current_task_id = None
        self.current_execution_id = None

        # Import Node.js hardware wrapper
        try:
            from nodejs_hardware import get_hardware_info

            self.get_hardware_info = get_hardware_info
            logger.info("Node.js hardware info wrapper loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import Node.js wrapper: {e}")
            logger.error(
                "Please ensure Node.js dependencies are installed: cd nodejs/hardware_info && npm install"
            )
            sys.exit(1)

        # Import script executor
        try:
            from script_executor import ScriptExecutor

            self.script_executor = ScriptExecutor(server_url, "")
        except ImportError:
            logger.warning("Script executor not available")
            self.script_executor = None

    def load_device_id(self) -> Optional[str]:
        """Load device ID from file"""
        try:
            if os.path.exists("device_id.txt"):
                with open("device_id.txt", "r") as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load device ID: {e}")
        return None

    def save_device_id(self, device_id: str):
        """Save device ID to file"""
        try:
            with open("device_id.txt", "w") as f:
                f.write(device_id)
        except Exception as e:
            logger.error(f"Failed to save device ID: {e}")

    def get_hostname(self) -> str:
        """Get hostname"""
        return socket.gethostname()

    def get_mac_address(self) -> str:
        """Get MAC address"""
        mac = ""
        try:
            # Get MAC from network interfaces
            import subprocess

            result = subprocess.run(
                ["getmac", "/v", "/fo", "csv"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(",")
                        if len(parts) >= 3:
                            mac = parts[2].strip().strip('"')
                            if mac and mac != "00-00-00-00-00-00":
                                break
        except:
            pass

        # Fallback
        if not mac or mac == "00-00-00-00-00-00":
            mac = "00-00-00-00-00-00"

        return mac.replace("-", ":")

    def get_ip_address(self) -> str:
        """Get IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(
                (
                    self.server_url.replace("http://", "")
                    .replace("https://", "")
                    .split(":")[0]
                    or "8.8.8.8",
                    80,
                )
            )
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def register_device(self) -> Optional[str]:
        """Register device with server"""
        try:
            # Get hardware info from Node.js
            hardware_info = self.get_hardware_info()

            if not hardware_info:
                logger.error("Failed to get hardware info from Node.js")
                return None

            # Get network info
            mac_address = self.get_mac_address()
            ip_address = self.get_ip_address()
            hostname = self.get_hostname()

            # Build registration payload
            payload = {
                "device_name": hostname,
                "hostname": hostname,
                "mac_address": mac_address,
                "ip_address": ip_address,
                "agent_version": self.CURRENT_VERSION,
                # Hardware info from Node.js
                "cpu_model": hardware_info.get("cpu_model"),
                "cpu_cores": hardware_info.get("cpu_cores"),
                "cpu_threads": hardware_info.get("cpu_threads"),
                "cpu_base_clock": hardware_info.get("cpu_base_clock"),
                "gpu_model": hardware_info.get("gpu_model"),
                "gpu_vram_mb": hardware_info.get("gpu_vram_mb"),
                "gpu_driver_version": hardware_info.get("gpu_driver_version"),
                "ram_total_gb": hardware_info.get("ram_total_gb"),
                "ram_frequency": hardware_info.get("ram_frequency"),
                "all_gpus": hardware_info.get("all_gpus"),
                "all_memory": hardware_info.get("all_memory"),
                "disk_model": hardware_info.get("disk_model"),
                "disk_capacity_tb": hardware_info.get("disk_capacity_tb"),
                "disk_type": hardware_info.get("disk_type"),
                "all_disks": hardware_info.get("all_disks"),
                "os_info": {
                    "os_name": hardware_info.get("os_name"),
                    "os_version": hardware_info.get("os_version"),
                    "os_build": hardware_info.get("os_build"),
                },
            }

            url = f"{self.server_url}/api/devices/agent/register"

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                device_data = response.json()
                device_id = device_data.get("id")
                if device_id:
                    self.save_device_id(device_id)
                    logger.info(f"Device registered successfully: {device_id}")
                    return device_id

            logger.error(
                f"Failed to register device: {response.status_code} {response.text}"
            )
            return None

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return None

    def send_heartbeat(
        self, status: str = "online", current_task_id: Optional[str] = None
    ):
        """Send heartbeat to server"""
        if not self.device_id:
            return

        try:
            payload = {
                "mac_address": self.get_mac_address(),
                "status": status,
            }

            if current_task_id:
                payload["current_task_id"] = current_task_id

            url = f"{self.server_url}/api/devices/agent/heartbeat"

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Heartbeat failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def poll_tasks(self):
        """Poll for pending tasks"""
        if not self.device_id:
            return None

        try:
            url = f"{self.server_url}/api/tasks/pending?device_id={self.device_id}"

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                tasks = response.json()
                if tasks:
                    return tasks[0]

        except Exception as e:
            logger.error(f"Failed to poll tasks: {e}")

        return None

    def run(self):
        """Main agent loop"""
        logger.info("Starting Hardware Benchmark Agent...")

        # Register or load device ID
        self.device_id = self.load_device_id()

        if not self.device_id:
            logger.info("Device not registered, registering...")
            self.device_id = self.register_device()

        if not self.device_id:
            logger.error("Cannot proceed without device ID")
            return

        logger.info(f"Agent running with device ID: {self.device_id}")

        # Send initial heartbeat
        self.send_heartbeat(status="online")

        # Main loop
        while self.running:
            try:
                # Send heartbeat
                self.send_heartbeat(
                    status="online", current_task_id=self.current_task_id
                )

                # Poll for tasks (only if not busy)
                if not self.current_task_id:
                    task = self.poll_tasks()
                    if task:
                        logger.info(f"Received task: {task.get('id')}")
                        # Process task (simplified - actual implementation would handle different task types)

                # Sleep before next iteration
                for _ in range(self.task_poll_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)

        # Send offline status before exit
        self.send_heartbeat(status="offline")
        logger.info("Agent stopped.")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Hardware Benchmark Agent")
    parser.add_argument(
        "--server", "-s", default="http://localhost:8000", help="Server URL"
    )
    parser.add_argument(
        "--api-key", "-k", default=None, help="API Key for authentication"
    )

    args = parser.parse_args()

    agent = HardwareBenchmarkAgent(args.server, args.api_key)
    agent.run()


if __name__ == "__main__":
    main()
