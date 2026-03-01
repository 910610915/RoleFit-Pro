# Hardware Benchmark Agent
# Runs on Windows devices to collect hardware info and report to server

import os
import sys
import json
import time
import socket
import logging
import platform
import uuid
import requests
import subprocess
import psutil
import wmi
import winreg
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

# Try to import updater
try:
    from updater import GitHubUpdater
except ImportError:
    GitHubUpdater = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HardwareCollector:
    """Collect hardware information from Windows system"""
    
    def __init__(self):
        self.wmi = wmi.WMI()
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        try:
            cpu = self.wmi.Win32_Processor()[0]
            return {
                "cpu_model": cpu.Name.strip() if cpu.Name else "Unknown",
                "cpu_cores": cpu.NumberOfCores,
                "cpu_threads": cpu.NumberOfLogicalProcessors
            }
        except Exception as e:
            logger.error(f"Failed to get CPU info: {e}")
            return {}

    def get_memory_info(self) -> Dict[str, Any]:
        """Get RAM information"""
        try:
            memory = self.wmi.Win32_PhysicalMemory()
            total_memory = sum(int(m.Capacity) for m in memory)
            total_gb = round(total_memory / (1024**3), 2)
            
            return {
                "ram_total_gb": total_gb
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {}
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        try:
            gpus = self.wmi.Win32_VideoController()
            gpu_list = []
            
            for gpu in gpus:
                vram_gb = None
                
                # Check for NVIDIA GPU and try nvidia-smi
                if 'NVIDIA' in (gpu.Name or '').upper():
                    try:
                        result = subprocess.run(
                            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            timeout=10 # Increased timeout
                        )
                        if result.returncode == 0:
                            # Take the first one if multiple lines, assuming first GPU
                            # Note: This might be inaccurate if multiple NVIDIA GPUs are present,
                            # but matches hardware_check.py logic
                            output = result.stdout.strip()
                            if output:
                                vram_mib = int(output.split('\n')[0])
                                vram_gb = round(vram_mib / 1024, 2)
                    except Exception as e:
                        logger.warning(f"nvidia-smi failed: {e}")
                
                if vram_gb is None:
                    if hasattr(gpu, 'AdapterRAM') and gpu.AdapterRAM:
                        # AdapterRAM is in bytes
                        try:
                            vram_gb = round(int(gpu.AdapterRAM) / (1024**3), 2)
                        except:
                            vram_gb = 0.0
                    else:
                        vram_gb = 0.0
                
                gpu_list.append({
                    "name": gpu.Name,
                    "vram_gb": vram_gb
                })
            
            # Find primary GPU (simply first one or first NVIDIA)
            primary_gpu = None
            if gpu_list:
                # Prefer NVIDIA
                for g in gpu_list:
                    if 'NVIDIA' in (g['name'] or '').upper():
                        primary_gpu = g
                        break
                if not primary_gpu:
                    primary_gpu = gpu_list[0]
            
            if primary_gpu:
                return {
                    "gpu_model": primary_gpu["name"],
                    "gpu_vram_mb": int(primary_gpu["vram_gb"] * 1024), # Convert back to MB for compatibility
                    "all_gpus": gpu_list
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return {}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get ALL disk information"""
        try:
            disks = self.wmi.Win32_DiskDrive()
            disk_list = []
            
            for disk in disks:
                size_gb = round(int(disk.Size) / (1024**3), 2) if disk.Size else 0
                interface = disk.Description # hardware_check uses Description as interface
                model = disk.Model
                
                # Better type detection logic
                disk_type = "Unknown"
                if "NVMe" in interface or "NVMe" in model:
                    disk_type = "NVMe"
                elif "SSD" in model or "Solid State" in model:
                    disk_type = "SSD"
                elif "USB" in interface or "USB" in model:
                    disk_type = "USB"
                elif "Fixed hard disk media" in interface: # Standard HDD description
                     # If it was SSD, it would likely be caught above or have SSD in model
                     # But some SSDs report as Fixed hard disk media. 
                     # Check rotation rate if possible? WMI doesn't easily give rotation rate without smart.
                     # Assume HDD if not marked as SSD/NVMe
                     disk_type = "HDD"
                
                disk_list.append({
                    "model": model,
                    "interface": interface,
                    "size_gb": size_gb,
                    # Add compatibility fields
                    "capacity_tb": round(size_gb / 1024, 2),
                    "type": disk_type
                })
            
            if disk_list:
                primary_disk = disk_list[0]
                return {
                    "disk_model": primary_disk["model"],
                    "disk_capacity_tb": primary_disk["capacity_tb"],
                    "disk_type": primary_disk["type"],
                    "all_disks": disk_list
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get disk info: {e}")
            return {}
    
    def get_os_info(self) -> Dict[str, Any]:
        """Get OS information"""
        try:
            # Use platform module first (more reliable)
            uname = platform.uname()
            
            # Try to get more detailed Windows info
            try:
                import winreg
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                
                # Get various OS info
                try:
                    build = winreg.QueryValueEx(reg_key, "CurrentBuild")[0]
                except:
                    build = ""
                
                try:
                    display_version = winreg.QueryValueEx(reg_key, "DisplayVersion")[0]
                except:
                    display_version = ""
                
                try:
                    edition = winreg.QueryValueEx(reg_key, "EditionID")[0]
                except:
                    edition = ""
                
                winreg.CloseKey(reg_key)
                
                os_version = f"{display_version} {edition}".strip() if display_version or edition else uname.release
                
            except Exception as e:
                logger.warning(f"Failed to read registry: {e}")
                os_version = uname.release
                build = uname.version
            
            return {
                "os_name": uname.system,  # "Windows"
                "os_version": os_version,
                "os_build": build if 'build' in dir() else uname.version
            }
        except Exception as e:
            logger.error(f"Failed to get OS info: {e}")
            return {"os_name": "Windows", "os_version": "Unknown", "os_build": "Unknown"}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            mac_address = ""
            ip_address = ""
            
            # Get MAC address
            for interface in psutil.net_if_addrs():
                if interface == "Ethernet" or interface == "Wi-Fi":
                    for addr in psutil.net_if_addrs()[interface]:
                        if addr.family == psutil.AF_LINK:
                            mac_address = addr.address
                        elif addr.family == psutil.AF_INET:
                            ip_address = addr.address
            
            # Fallback: get any available MAC
            if not mac_address:
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:
                            mac_address = addr.address
                            break
                    if mac_address:
                        break
            
            # Get hostname
            hostname = socket.gethostname()
            
            return {
                "mac_address": mac_address.upper(),
                "ip_address": ip_address,
                "hostname": hostname
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {}
    
    def get_all_hardware_info(self) -> Dict[str, Any]:
        """Get all hardware information"""
        info = {}
        info.update(self.get_cpu_info())
        info.update(self.get_gpu_info())
        info.update(self.get_memory_info())
        info.update(self.get_disk_info())
        info.update(self.get_os_info())
        info.update(self.get_network_info())
        return info


class SystemMonitor:
    """Monitor real-time system metrics"""
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            
            # Get process count
            process_count = len(psutil.pids())
            
            return {
                "cpu_usage_percent": cpu_percent,
                "ram_usage_percent": memory.percent,
                "ram_used_gb": round(memory.used / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "process_count": process_count
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}


class HardwareBenchmarkAgent:
    """Main agent class for hardware benchmark reporting"""
    
    # GitHub update configuration
    GITHUB_OWNER = "910610915" # 请根据实际情况修改
    GITHUB_REPO = "RoleFit-Pro" # 请根据实际情况修改
    CURRENT_VERSION = "1.0.2"  # 当前版本号
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.device_id = None
        self.collector = HardwareCollector()
        self.monitor = SystemMonitor()
        self.running = True
        self.heartbeat_interval = 60  # seconds
        self.task_poll_interval = 10  # seconds
        self.current_task_id = None
        self.current_execution_id = None
        
        # Initialize updater
        self.updater = None
        if GitHubUpdater:
            self.updater = GitHubUpdater(
                self.GITHUB_OWNER, 
                self.GITHUB_REPO, 
                self.CURRENT_VERSION
            )
        
        # Import script executor
        try:
            from script_executor import ScriptExecutor, MetricsCollector
            self.script_executor = ScriptExecutor(server_url, "")
            self.metrics_collector = MetricsCollector()
        except ImportError:
            logger.warning("Script executor not available")
            self.script_executor = None
            self.metrics_collector = None
        
        # Import software manager
        try:
            from software_manager import SoftwareManager
            self.software_manager = SoftwareManager(server_url)
        except ImportError:
            logger.warning("Software manager not available")
            self.software_manager = None
    
    def get_or_create_device_id(self) -> str:
        """Get device ID from file or create new one"""
        device_file = "device_id.txt"
        if os.path.exists(device_file):
            with open(device_file, 'r') as f:
                return f.read().strip()
        else:
            device_id = str(uuid.uuid4())
            with open(device_file, 'w') as f:
                f.write(device_id)
            return device_id
    
    def register_device(self, hardware_info: Dict[str, Any]) -> bool:
        """Register device with server"""
        try:
            url = f"{self.server_url}/api/devices/agent/register"
            
            # Get device name from hostname
            device_name = socket.gethostname()
            
            data = {
                "device_name": device_name,
                "hostname": hardware_info.get("hostname", device_name),
                "mac_address": hardware_info.get("mac_address", ""),
                "ip_address": hardware_info.get("ip_address", ""),
                "agent_version": "1.0.0",
                "os_info": {
                    "os_name": hardware_info.get("os_name", ""),
                    "os_version": hardware_info.get("os_version", ""),
                    "os_build": hardware_info.get("os_build", "")
                }
            }
            
            # Add hardware info to registration
            for key, value in hardware_info.items():
                if key not in ["mac_address", "ip_address", "hostname"]:
                    data[key] = value
            
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"Device registered successfully: {device_name}")
                return True
            else:
                logger.error(f"Failed to register device: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def send_heartbeat(self, status: str = "online", current_task_id: Optional[str] = None) -> bool:
        """Send heartbeat to server"""
        try:
            url = f"{self.server_url}/api/devices/agent/heartbeat"
            
            # Get current system metrics
            metrics = self.monitor.get_current_metrics()
            
            data = {
                "mac_address": self.get_mac_address(),
                "status": status,
                "current_task_id": current_task_id,
                "system_info": metrics
            }
            
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    def get_mac_address(self) -> str:
        """Get MAC address"""
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        return addr.address.upper()
        except:
            pass
        return ""
    
    def poll_tasks(self) -> List[Dict[str, Any]]:
        """Poll server for pending tasks"""
        try:
            url = f"{self.server_url}/api/agent/tasks/pending"
            params = {"device_id": self.device_id}
            
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to poll tasks: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error polling tasks: {e}")
            return []
    
    def start_execution(self, script_id: Optional[str], task_id: Optional[str]) -> Optional[str]:
        """Notify server that execution is starting"""
        try:
            url = f"{self.server_url}/api/agent/executions/start"
            params = {
                "script_id": script_id or "",
                "device_id": self.device_id,
                "task_id": task_id or ""
            }
            
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.post(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("execution_id")
            else:
                logger.warning(f"Failed to start execution: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting execution: {e}")
            return None
    
    def _report_software_error(self, task_id: str, error_message: str):
        """上报软件安装错误到服务器"""
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/software_error"
            data = {
                "error_type": "software_install",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id
            }
            requests.post(url, json=data, timeout=10)
            logger.info(f"Reported software error to server: {error_message}")
        except Exception as e:
            logger.error(f"Failed to report software error: {e}")
        
        # 更新任务状态
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/complete"
            requests.put(url, json={
                "task_status": "failed",
                "error_message": error_message
            }, timeout=10)
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    def complete_execution(self, execution_id: str, exit_code: int = 0, 
                          error_message: str = None, metrics: List[Dict] = None):
        """Notify server that execution is complete"""
        try:
            url = f"{self.server_url}/api/agent/executions/{execution_id}/complete"
            
            # All data in body
            data = {
                "exit_code": exit_code,
                "error_message": error_message or "",
                "metrics_data": metrics or []
            }
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.put(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Execution completed: {execution_id}")
                return True
            else:
                logger.warning(f"Failed to complete execution: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing execution: {e}")
            return False
    
    def execute_task(self, task: Dict[str, Any]):
        """Execute a single task"""
        if not self.script_executor:
            logger.warning("Script executor not available")
            return
        
        task_id = task.get("task_id")
        task_name = task.get("task_name")
        task_type = task.get("task_type", "benchmark")
        duration = task.get("test_duration_seconds") or 60
        
        logger.info(f"Executing task: {task_name} (task_id: {task_id}, type: {task_type})")
        
        # ====== 软件准备阶段 ======
        software_list = task.get("software_list", [])
        software_error = None
        
        if software_list and self.software_manager:
            logger.info(f"Preparing software for task (count: {len(software_list)})")
            
            for software in software_list:
                software_name = software.get('software_name', software.get('software_code', 'unknown'))
                logger.info(f"Checking software: {software_name}")
                
                # 1. 检测是否已安装
                is_installed = self.software_manager.check_installed(software)
                
                if is_installed:
                    logger.info(f"Software {software_name} already installed")
                    continue
                
                logger.info(f"Software {software_name} not found, preparing to install...")
                
                # 2. 下载软件
                software_code = software.get('software_code')
                package_path = self.software_manager.download(software_code)
                
                if not package_path:
                    software_error = f"Failed to download {software_name}"
                    logger.error(software_error)
                    break
                
                # 3. 安装/解压软件
                install_result = self.software_manager.install(package_path, software)
                
                if not install_result.get('success'):
                    software_error = f"Failed to install {software_name}: {install_result.get('error', 'Unknown error')}"
                    logger.error(software_error)
                    break
                
                logger.info(f"Software {software_name} installed successfully")
            
            # 如果有软件错误，上报并终止任务
            if software_error:
                self._report_software_error(task_id, software_error)
                return
        
        # ====== 正常执行测试 ======
        
        # First, update task status to running via API
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/execute"
            requests.post(url, json={"device_ids": [self.device_id]}, timeout=10)
        except Exception as e:
            logger.warning(f"Failed to update task status to running: {e}")
        
        # Notify server that execution is starting
        # For benchmark tasks, we use task_id as script_id
        execution_id = self.start_execution(task_id, task_id)
        if not execution_id:
            logger.error("Failed to start execution")
            return
        
        self.current_task_id = task_id
        self.current_execution_id = execution_id
        
        # Update status to running
        self.send_heartbeat(status="testing", current_task_id=task_id)
        
        # Prepare script config based on task type
        script_config = {
            "action": "benchmark",
            "benchmark_type": task_type,
            "expected_duration": duration
        }
        
        # Add software info if available
        software = task.get("software", {})
        if software:
            script_config["action"] = "launch"
            script_config["path"] = software.get("path", "")
            script_config["params"] = software.get("params", "")
            script_config["process"] = software.get("name", "").split()[0] if software.get("name") else ""
        
        # Execute script and collect metrics
        metrics_history = []
        
        try:
            # Start metrics collection in background
            if self.metrics_collector:
                collection_thread = threading.Thread(
                    target=self._collect_metrics_loop,
                    args=(60, metrics_history)
                )
                collection_thread.daemon = True
                collection_thread.start()
            
            # Execute the script
            result = self.script_executor.execute_script(script_config)
            
            # Stop metrics collection
            self.script_executor.collecting = False
            
            # Complete execution
            self.complete_execution(
                execution_id=execution_id,
                exit_code=result.get("exit_code", 0) if result.get("success") else -1,
                error_message=result.get("error_message"),
                metrics=metrics_history
            )
            
            logger.info(f"Task completed: {task_id}, success: {result.get('success')}")
            
            # Update task status to completed
            try:
                url = f"{self.server_url}/api/tasks/{task_id}/complete"
                params = {"task_status": "completed"}
                requests.post(url, params=params, timeout=10)
            except Exception as e:
                logger.warning(f"Failed to update task status: {e}")
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            self.complete_execution(
                execution_id=execution_id,
                exit_code=-1,
                error_message=str(e)
            )
        
        finally:
            self.current_task_id = None
            self.current_execution_id = None
            self.send_heartbeat(status="online")
    
    def _collect_metrics_loop(self, duration: int, history: List[Dict]):
        """Background thread to collect metrics during execution"""
        start_time = time.time()
        
        while self.script_executor and self.script_executor.collecting:
            if time.time() - start_time >= duration:
                break
            
            try:
                sys_metrics = self.metrics_collector.get_system_metrics()
                gpu_metrics = self.metrics_collector.get_gpu_metrics()
                
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    **sys_metrics,
                    **gpu_metrics
                }
                
                history.append(metrics)
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
    
    def process_tasks(self):
        """Poll and process pending tasks"""
        if self.current_task_id:
            # Already running a task
            return
        
        tasks = self.poll_tasks()
        
        if tasks:
            logger.info(f"Found {len(tasks)} pending tasks")
            for task in tasks:
                self.execute_task(task)
                # Process one task at a time
                break
    
    def check_and_perform_updates(self):
        """Check for updates and perform if available"""
        if not self.updater:
            return
            
        try:
            logger.info("Performing update check...")
            release = self.updater.check_for_updates()
            if release:
                self.updater.perform_update(release)
        except Exception as e:
            logger.error(f"Update check error: {e}")

    def send_metrics(self) -> bool:
        """Send real-time performance metrics to server"""
        try:
            url = f"{self.server_url}/api/performance/metrics"
            
            # Get current system metrics
            sys_metrics = self.monitor.get_current_metrics()
            
            # Map SystemMonitor metrics to PerformanceMetricCreate schema
            # SystemMonitor returns: cpu_usage_percent, ram_usage_percent, ram_used_gb, disk_usage_percent, process_count
            # PerformanceMetricCreate expects: cpu_percent, memory_percent, memory_used_mb, disk_io_percent, etc.
            
            data = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": sys_metrics.get("cpu_usage_percent"),
                "memory_percent": sys_metrics.get("ram_usage_percent"),
                "memory_used_mb": sys_metrics.get("ram_used_gb", 0) * 1024, # Convert GB to MB
                # "disk_io_percent": sys_metrics.get("disk_usage_percent"), # Map disk usage to io_percent for now or just ignore? 
                # Actually disk_usage_percent is space usage, not performance metric. 
                # Let's add disk_io_percent to SystemMonitor or just leave it None for now.
                "process_count": sys_metrics.get("process_count")
            }
            
            # Add GPU metrics if available (reuse logic from collector or monitor)
            # SystemMonitor currently doesn't have GPU.
            # We can try to get simple GPU usage if nvidia-smi is available
            try:
                # Simple NVIDIA GPU check
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        # "50, 4096, 8192"
                        parts = output.split(', ')
                        if len(parts) >= 3:
                            data["gpu_percent"] = float(parts[0])
                            data["gpu_memory_used_mb"] = float(parts[1])
                            data["gpu_memory_total_mb"] = float(parts[2])
            except:
                pass

            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 201:
                return True
            else:
                logger.warning(f"Metrics push failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Metrics push error: {e}")
            return False

    def run(self):
        """Main agent loop"""
        logger.info(f"Starting Hardware Benchmark Agent v{self.CURRENT_VERSION}...")
        
        # Cleanup old updates
        if getattr(sys, 'frozen', False):
            old_exe = sys.executable + ".old"
            if os.path.exists(old_exe):
                try:
                    os.remove(old_exe)
                    logger.info("Cleaned up old version backup.")
                except:
                    pass
        
        # Initial update check
        self.check_and_perform_updates()
        
        # Get device ID
        self.device_id = self.get_or_create_device_id()
        
        # Collect hardware info and register
        hardware_info = self.collector.get_all_hardware_info()
        logger.info(f"Hardware Info: {json.dumps(hardware_info, indent=2)}")
        
        # Register with server
        if not self.register_device(hardware_info):
            logger.error("Failed to register device. Retrying in 30 seconds...")
            time.sleep(30)
            if not self.register_device(hardware_info):
                logger.error("Registration failed twice. Exiting.")
                return
        
        # Main loop
        logger.info("Agent running. Press Ctrl+C to stop.")
        
        last_update_check = time.time()
        last_metrics_push = 0
        UPDATE_CHECK_INTERVAL = 3600 * 24  # Check daily
        METRICS_PUSH_INTERVAL = 10 # Push metrics every 10 seconds
        
        while self.running:
            try:
                current_time = time.time()
                
                # Periodic update check
                if current_time - last_update_check > UPDATE_CHECK_INTERVAL:
                    if not self.current_task_id:  # Only check if idle
                        self.check_and_perform_updates()
                        last_update_check = current_time
                
                # Send heartbeat
                status = "testing" if self.current_task_id else "online"
                self.send_heartbeat(status=status, current_task_id=self.current_task_id)
                
                # Push performance metrics
                if current_time - last_metrics_push > METRICS_PUSH_INTERVAL:
                    self.send_metrics()
                    last_metrics_push = current_time
                
                # Poll for tasks
                if not self.current_task_id:
                    self.process_tasks()
                
                # Sleep less frequently when idle
                time.sleep(self.task_poll_interval if not self.current_task_id else self.heartbeat_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping agent...")
                self.running = False
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
    parser.add_argument("--server", "-s", default="http://localhost:8000", 
                        help="Server URL")
    parser.add_argument("--api-key", "-k", default=None,
                        help="API Key for authentication")
    
    args = parser.parse_args()
    
    agent = HardwareBenchmarkAgent(args.server, args.api_key)
    agent.run()


if __name__ == "__main__":
    main()
