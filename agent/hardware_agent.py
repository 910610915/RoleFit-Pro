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

        # Import Performance Monitor
        try:
            from hardware_monitor import PerformanceMonitor
            self.PerformanceMonitor = PerformanceMonitor
        except ImportError:
            logger.warning("Performance Monitor not available")
            self.PerformanceMonitor = None
            
        self.monitor = None
        self.monitor_thread = None

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
                if tasks and isinstance(tasks, list):
                    return tasks[0]
                elif tasks and isinstance(tasks, dict) and "items" in tasks:
                    # Handle paginated response
                    if tasks["items"]:
                        return tasks["items"][0]

        except Exception as e:
            logger.error(f"Failed to poll tasks: {e}")

        return None

    def poll_control_commands(self):
        """Poll for pending control commands"""
        if not self.device_id:
            return None

        try:
            url = f"{self.server_url}/api/performance/commands/pending?device_id={self.device_id}"

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Handle paginated response
                if isinstance(data, dict) and "items" in data:
                    commands = data["items"]
                    if commands:
                        return commands[0]
                # Handle list response (fallback)
                elif isinstance(data, list) and data:
                    return data[0]

        except Exception as e:
            logger.error(f"Failed to poll control commands: {e}")

        return None

    def execute_control_command(self, command: dict):
        """Execute a control command"""
        import subprocess
        import os

        command_id = command.get("id")
        command_type = command.get("command_type")

        logger.info(f"Executing control command: {command_type} (ID: {command_id})")

        try:
            # Update command status to executing
            self._update_command_status(command_id, "executing")

            result = None
            error_message = None

            if command_type == "shutdown":
                # Windows shutdown command
                subprocess.run(
                    ["shutdown", "/s", "/t", "60", "/c", "Remote shutdown initiated"],
                    capture_output=True,
                    timeout=10,
                )
                result = "Shutdown command sent (60 second delay)"

            elif command_type == "restart":
                # Windows restart command
                subprocess.run(
                    ["shutdown", "/r", "/t", "60", "/c", "Remote restart initiated"],
                    capture_output=True,
                    timeout=10,
                )
                result = "Restart command sent (60 second delay)"

            elif command_type == "lock":
                # Lock workstation
                subprocess.run(
                    ["rundll32.exe", "user32.dll,LockWorkStation"],
                    capture_output=True,
                    timeout=10,
                )
                result = "Workstation locked"

            elif command_type == "unlock":
                # Note: Cannot programmatically unlock
                error_message = "Cannot remotely unlock - requires physical interaction"
                logger.warning(error_message)

            elif command_type == "execute":
                # Execute custom command
                import json

                params = json.loads(command.get("command_params", "{}"))
                cmd = params.get("command", "")
                if cmd:
                    proc = subprocess.run(
                        cmd, shell=True, capture_output=True, timeout=300
                    )
                    result = (
                        proc.stdout.decode("utf-8", errors="ignore")[:1000]
                        if proc.stdout
                        else ""
                    )
                    if proc.returncode != 0:
                        error_message = proc.stderr.decode("utf-8", errors="ignore")[
                            :500
                        ]
                else:
                    error_message = "No command specified"

            else:
                error_message = f"Unknown command type: {command_type}"

            # Update command status
            if error_message:
                self._update_command_status(
                    command_id, "failed", error_message=error_message
                )
            else:
                self._update_command_status(command_id, "completed", result=result)

        except subprocess.TimeoutExpired:
            self._update_command_status(
                command_id, "failed", error_message="Command timeout"
            )
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            self._update_command_status(command_id, "failed", error_message=str(e))

    def _update_command_status(
        self,
        command_id: str,
        status: str,
        result: str = None,
        error_message: str = None,
    ):
        """Update command status on server"""
        try:
            import json

            url = f"{self.server_url}/api/performance/commands/{command_id}/complete"
            if status == "executing":
                url = f"{self.server_url}/api/performance/commands/{command_id}/acknowledge"

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            payload = {}
            if status == "completed":
                if result:
                    payload["result"] = result
            elif status == "failed":
                if error_message:
                    payload["error_message"] = error_message

            requests.post(url, json=payload, headers=headers, timeout=10)
            logger.info(f"Command {command_id} status updated to: {status}")

        except Exception as e:
            logger.error(f"Failed to update command status: {e}")

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

        # Start performance monitor
        if self.PerformanceMonitor and self.device_id:
            logger.info("Starting performance monitor...")
            try:
                self.monitor = self.PerformanceMonitor(self.device_id, self.server_url, self.api_key)
                self.monitor_thread = threading.Thread(target=self.monitor.run)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
            except Exception as e:
                logger.error(f"Failed to start performance monitor: {e}")

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

                # Poll for control commands (only if not busy)
                if not self.current_task_id:
                    control_cmd = self.poll_control_commands()
                    if control_cmd:
                        logger.info(
                            f"Received control command: {control_cmd.get('command_type')}"
                        )
                        self.execute_control_command(control_cmd)

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

        # Stop performance monitor
        if self.monitor:
            logger.info("Stopping performance monitor...")
            self.monitor.stop()
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)

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
