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
            cpu_info = {}
            for cpu in self.wmi.Win32_Processor():
                cpu_info = {
                    "cpu_model": cpu.Name.strip() if cpu.Name else "Unknown",
                    "cpu_cores": cpu.NumberOfCores,
                    "cpu_threads": cpu.NumberOfLogicalProcessors,
                    "cpu_base_clock": round(cpu.MaxClockSpeed / 1000, 2) if cpu.MaxClockSpeed else None
                }
                break
            return cpu_info
        except Exception as e:
            logger.error(f"Failed to get CPU info: {e}")
            return {}

    def _get_nvidia_vram(self) -> Optional[int]:
        """Get NVIDIA GPU VRAM using nvidia-smi (more accurate)"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            if result.returncode == 0:
                vram_mib = int(result.stdout.strip().split('\n')[0])
                return vram_mib
        except Exception as e:
            logger.debug(f"nvidia-smi not available: {e}")
        return None
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information - all GPUs"""
        try:
            gpus = []
            # Keywords to exclude virtual/display adapters
            exclude_keywords = [
                "virtual", "display", "basic", "microsoft", "standard",
                "ramd", "llvmpipe", "softpipe", "swrast", "nvidiagt"
            ]
            
            # Try to get accurate NVIDIA VRAM first
            nvidia_vram_mb = self._get_nvidia_vram()
            
            for gpu in self.wmi.Win32_VideoController():
                try:
                    vram_mb = 0
                    gpu_name = gpu.Name.strip() if gpu.Name else "Unknown"
                    
                    # Use nvidia-smi if available and this is an NVIDIA GPU
                    if nvidia_vram_mb and 'NVIDIA' in gpu_name.upper():
                        vram_mb = nvidia_vram_mb
                    else:
                        # Fallback to WMI
                        vram_bytes = int(gpu.AdapterRAM) if gpu.AdapterRAM else 0
                        vram_mb = vram_bytes // (1024 * 1024) if vram_bytes > 0 else 0
                    
                    # Skip virtual/display adapters
                    gpu_name_lower = gpu_name.lower()
                    is_virtual = any(kw in gpu_name_lower for kw in exclude_keywords)
                    
                    gpus.append({
                        "name": gpu_name,
                        "vram_mb": vram_mb,
                        "driver_version": gpu.DriverVersion if gpu.DriverVersion else "",
                        "is_virtual": is_virtual
                    })
                except Exception as e:
                    logger.warning(f"Failed to get GPU info: {e}")
            
            # Filter out virtual GPUs and find the best discrete GPU
            real_gpus = [g for g in gpus if not g.get("is_virtual", True)]
            
            # If we have real GPUs, use the first one as primary
            if real_gpus:
                primary = real_gpus[0]
                return {
                    "gpu_model": primary["name"],
                    "gpu_vram_mb": primary["vram_mb"],
                    "gpu_driver_version": primary["driver_version"],
                    "all_gpus": gpus  # Store all GPUs including virtual
                }
            # Fallback to first GPU if no real GPU found
            elif gpus:
                return {
                    "gpu_model": gpus[0]["name"],
                    "gpu_vram_mb": gpus[0]["vram_mb"],
                    "gpu_driver_version": gpus[0]["driver_version"],
                    "all_gpus": gpus
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return {}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get RAM information with details"""
        try:
            mem = psutil.virtual_memory()
            
            # Get memory slots info via WMI
            memory_modules = []
            try:
                for mem_module in self.wmi.Win32_PhysicalMemory():
                    try:
                        speed = mem_module.Speed if hasattr(mem_module, 'Speed') and mem_module.Speed else 0
                        capacity_bytes = int(mem_module.Capacity) if mem_module.Capacity else 0
                        capacity_mb = capacity_bytes // (1024 * 1024)
                        
                        memory_modules.append({
                            "capacity_mb": capacity_mb,
                            "speed": speed,
                            "manufacturer": getattr(mem_module, 'Manufacturer', '') or ''
                        })
                    except:
                        pass
            except:
                pass
            
            total_gb = round(mem.total / (1024**3), 2)
            
            # Calculate number of sticks
            num_sticks = len(memory_modules) if memory_modules else 1
            
            # Get average frequency if available
            frequencies = [m["speed"] for m in memory_modules if m["speed"] > 0]
            avg_frequency = sum(frequencies) // len(frequencies) if frequencies else None
            
            return {
                "ram_total_gb": total_gb,
                "ram_frequency": avg_frequency,
                "ram_sticks": num_sticks,
                "ram_details": memory_modules
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {"ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get ALL disk information"""
        try:
            disks = []
            
            # NVMe SSD brand/model keywords
            nvme_keywords = [
                "nvme", "samsung", "wd", "western", "sn", "980", "990",
                "gammix", "zhitai", "tiplus", "corsair", "crucial", 
                "kingston", "intel", "sabrent", "adata", "p5", "p5+"
            ]
            
            for disk in self.wmi.Win32_DiskDrive():
                try:
                    size_bytes = int(disk.Size) if disk.Size else 0
                    capacity_tb = round(size_bytes / (1024**4), 2) if size_bytes > 0 else 0
                    
                    # Determine disk type
                    model = disk.Model.lower() if disk.Model else ""
                    media_type = getattr(disk, 'MediaType', '') or ''
                    interface = getattr(disk, 'InterfaceType', '') or ''
                    
                    # Check NVMe via interface type first (most reliable)
                    if interface.lower() == "nvme" or "nvme" in interface.lower():
                        disk_type = "NVMe"
                    # Check via media type
                    elif "nvme" in media_type.lower():
                        disk_type = "NVMe"
                    elif "ssd" in media_type.lower():
                        disk_type = "SSD"
                    elif "hdd" in media_type.lower() or "hard disk" in media_type.lower():
                        disk_type = "HDD"
                    # Check via model name for known NVMe SSD brands
                    elif any(kw in model for kw in nvme_keywords):
                        if size_bytes > 0:
                            capacity_gb = size_bytes / (1024**3)
                            # Larger SSDs (>256GB) are likely NVMe
                            if capacity_gb > 256:
                                disk_type = "NVMe"
                            else:
                                disk_type = "SSD"
                        else:
                            disk_type = "SSD"
                    else:
                        disk_type = "Unknown"
                    
                    disks.append({
                        "model": disk.Model.strip() if disk.Model else "Unknown",
                        "capacity_tb": capacity_tb,
                        "type": disk_type,
                        "interface": interface
                    })
                except Exception as e:
                    logger.warning(f"Failed to get disk info: {e}")
            
            # Return first disk as primary
            if disks:
                return {
                    "disk_model": disks[0]["model"],
                    "disk_capacity_tb": disks[0]["capacity_tb"],
                    "disk_type": disks[0]["type"],
                    "all_disks": disks
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
    
    def run(self):
        """Main agent loop"""
        logger.info("Starting Hardware Benchmark Agent...")
        
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
        
        while self.running:
            try:
                # Send heartbeat
                status = "testing" if self.current_task_id else "online"
                self.send_heartbeat(status=status, current_task_id=self.current_task_id)
                
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
