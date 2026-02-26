# Script Executor for Hardware Benchmark Agent
# Executes job simulation scripts and collects performance metrics

import os
import sys
import json
import time
import logging
import subprocess
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
import psutil
import wmi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect system performance metrics"""
    
    def __init__(self):
        self.wmi = wmi.WMI()
        self.gpu_utilization = 0
        self.gpu_memory_used = 0
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Network
            net_io = psutil.net_io_counters()
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "memory_available_mb": memory.available / (1024 * 1024),
            }
            
            # Add disk metrics if available
            if disk_io:
                metrics["disk_read_mbps"] = disk_io.read_bytes / (1024 * 1024) / 0.5  # MB/s
                metrics["disk_write_mbps"] = disk_io.write_bytes / (1024 * 1024) / 0.5
            
            # Add network metrics if available
            if net_io:
                metrics["network_sent_mb"] = net_io.bytes_sent / (1024 * 1024)
                metrics["network_recv_mb"] = net_io.bytes_recv / (1024 * 1024)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_gpu_metrics(self) -> Dict[str, Any]:
        """Get GPU metrics using WMI"""
        try:
            for gpu in self.wmi.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine():
                # GPU engine utilization
                self.gpu_utilization = gpu.UtilizationPercentage
                break
            
            for gpu in self.wmi.Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory():
                # GPU memory usage
                self.gpu_memory_used = gpu.SharedUsage + gpu.DedicatedUsage
                break
            
            return {
                "gpu_percent": self.gpu_utilization,
                "gpu_memory_mb": self.gpu_memory_used / (1024 * 1024) if self.gpu_memory_used else 0
            }
        except Exception as e:
            # GPU metrics may not be available on all systems
            return {
                "gpu_percent": 0,
                "gpu_memory_mb": 0
            }
    
    def get_process_metrics(self, process_name: str) -> Dict[str, Any]:
        """Get metrics for a specific process"""
        try:
            for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info']):
                try:
                    if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                        # Get CPU percent with interval
                        cpu = proc.cpu_percent(interval=0.1)
                        mem_info = proc.memory_info()
                        
                        return {
                            "process_name": proc.info['name'],
                            "pid": proc.info['pid'],
                            "cpu_percent": cpu,
                            "memory_mb": mem_info.rss / (1024 * 1024),
                            "found": True
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {"found": False}
        except Exception as e:
            logger.error(f"Failed to get process metrics: {e}")
            return {"found": False}


class ScriptExecutor:
    """Execute job simulation scripts"""
    
    def __init__(self, server_url: str, device_id: str):
        self.server_url = server_url
        self.device_id = device_id
        self.metrics_collector = MetricsCollector()
        self.current_process: Optional[subprocess.Popen] = None
        self.metrics_thread: Optional[threading.Thread] = None
        self.collecting = False
        self.metrics_history: List[Dict[str, Any]] = []
    
    def parse_script_content(self, script_content: str) -> Dict[str, Any]:
        """Parse JSON script content"""
        try:
            return json.loads(script_content)
        except json.JSONDecodeError:
            logger.error(f"Invalid script content: {script_content}")
            return {}
    
    def launch_application(self, app_path: str, params: str = "") -> bool:
        """Launch application"""
        try:
            # Check if file exists
            if not os.path.exists(app_path):
                logger.error(f"Application not found: {app_path}")
                return False
            
            # Build command
            cmd = f'"{app_path}"'
            if params:
                cmd += f" {params}"
            
            logger.info(f"Launching: {cmd}")
            
            # Start process
            self.current_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            logger.info(f"Process started with PID: {self.current_process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return False
    
    def wait_for_process(self, process_name: str, timeout: int = 30) -> bool:
        """Wait for process to start"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            metrics = self.metrics_collector.get_process_metrics(process_name)
            if metrics.get("found"):
                logger.info(f"Process {process_name} found with PID: {metrics.get('pid')}")
                return True
            time.sleep(0.5)
        return False
    
    def stop_process(self, process_name: str) -> bool:
        """Stop process by name"""
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                        logger.info(f"Stopping process: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=5)
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
            return False
        except Exception as e:
            logger.error(f"Failed to stop process: {e}")
            return False
    
    def collect_metrics_loop(self, duration: int, interval: float = 1.0):
        """Background thread to collect metrics"""
        start_time = time.time()
        
        while self.collecting and (time.time() - start_time) < duration:
            try:
                # System metrics
                sys_metrics = self.metrics_collector.get_system_metrics()
                gpu_metrics = self.metrics_collector.get_gpu_metrics()
                
                # Combine metrics
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    **sys_metrics,
                    **gpu_metrics
                }
                
                self.metrics_history.append(metrics)
                logger.debug(f"Metrics: {json.dumps(metrics)}")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
    
    def execute_script(self, script_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a script and collect metrics"""
        
        # 支持两种格式：
        # 1. 直接传入script_content (从服务器获取的格式)
        # 2. 直接传入action等字段 (测试用格式)
        script_content = script_config.get("script_content")
        if script_content:
            script = self.parse_script_content(script_content)
        else:
            # 测试用格式：直接使用script_config
            script = script_config
        
        action = script.get("action", "")
        app_path = script.get("path", "")
        params = script.get("params", "")
        process_name = script.get("process", "")
        
        # 从script_config或script中获取duration
        duration = script_config.get("expected_duration") or script.get("duration", 60)
        
        result = {
            "success": False,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "exit_code": -1,
            "error_message": "",
            "metrics_summary": {}
        }
        
        try:
            if action == "benchmark":
                # Run benchmark test
                benchmark_type = script.get("benchmark_type", "full")
                logger.info(f"Running benchmark test: {benchmark_type}")
                
                try:
                    from benchmark import BenchmarkRunner
                    benchmark_result = BenchmarkRunner.run_benchmark(benchmark_type, duration)
                    result["success"] = True
                    result["exit_code"] = 0
                    result["metrics_summary"] = benchmark_result
                except Exception as e:
                    result["error_message"] = f"Benchmark failed: {str(e)}"
                    logger.error(f"Benchmark error: {e}")
                
            elif action == "launch":
                # Launch application
                if not self.launch_application(app_path, params):
                    result["error_message"] = "Failed to launch application"
                    return result
                
                # Wait for process to start
                if process_name:
                    if not self.wait_for_process(process_name, timeout=30):
                        result["error_message"] = "Process did not start"
                        return result
                
                # Start metrics collection in background
                self.collecting = True
                self.metrics_history = []
                self.metrics_thread = threading.Thread(
                    target=self.collect_metrics_loop,
                    args=(duration, 1.0)
                )
                self.metrics_thread.start()
                
                # Wait for duration
                logger.info(f"Collecting metrics for {duration} seconds...")
                time.sleep(duration)
                
                # Stop collection
                self.collecting = False
                if self.metrics_thread:
                    self.metrics_thread.join(timeout=5)
                
                # Stop the process
                if process_name:
                    self.stop_process(process_name)
                
                # Calculate metrics summary
                if self.metrics_history:
                    cpu_values = [m.get("cpu_percent", 0) for m in self.metrics_history]
                    mem_values = [m.get("memory_percent", 0) for m in self.metrics_history]
                    gpu_values = [m.get("gpu_percent", 0) for m in self.metrics_history]
                    
                    result["metrics_summary"] = {
                        "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                        "max_cpu_percent": max(cpu_values) if cpu_values else 0,
                        "avg_memory_percent": sum(mem_values) / len(mem_values) if mem_values else 0,
                        "max_memory_percent": max(mem_values) if mem_values else 0,
                        "avg_gpu_percent": sum(gpu_values) / len(gpu_values) if gpu_values else 0,
                        "max_gpu_percent": max(gpu_values) if gpu_values else 0,
                        "sample_count": len(self.metrics_history)
                    }
                
                result["success"] = True
                result["exit_code"] = 0
                
            elif action == "wait":
                # Just wait for specified duration
                logger.info(f"Waiting for {duration} seconds...")
                time.sleep(duration)
                result["success"] = True
                
            else:
                result["error_message"] = f"Unknown action: {action}"
                
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"Script execution error: {e}")
        
        finally:
            # Cleanup
            self.collecting = False
            if self.metrics_thread and self.metrics_thread.is_alive():
                self.metrics_thread.join(timeout=2)
            
            result["end_time"] = datetime.utcnow().isoformat()
            if result["start_time"] and result["end_time"]:
                start = datetime.fromisoformat(result["start_time"])
                end = datetime.fromisoformat(result["end_time"])
                result["duration_seconds"] = int((end - start).total_seconds())
        
        return result
    
    def execute_script_from_server(self, script_id: str, execution_id: str) -> Dict[str, Any]:
        """Execute a script from server configuration"""
        try:
            import requests
            
            # Get script config from server
            url = f"{self.server_url}/api/scripts/{script_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {"success": False, "error_message": f"Failed to get script: {response.status_code}"}
            
            script_config = response.json()
            
            # Execute
            result = self.execute_script(script_config)
            
            # Report result to server
            self.report_execution_result(execution_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute script from server: {e}")
            return {"success": False, "error_message": str(e)}
    
    def report_execution_result(self, execution_id: str, result: Dict[str, Any]):
        """Report execution result to server"""
        try:
            import requests
            
            url = f"{self.server_url}/api/executions/{execution_id}"
            data = {
                "end_time": result.get("end_time"),
                "duration_seconds": result.get("duration_seconds"),
                "exit_code": result.get("exit_code", 0),
                "error_message": result.get("error_message", "")
            }
            
            response = requests.put(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Execution result reported: {execution_id}")
            else:
                logger.warning(f"Failed to report result: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to report execution result: {e}")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script Executor for Hardware Benchmark")
    parser.add_argument("--server", "-s", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--device", "-d", default="test-device", help="Device ID")
    args = parser.parse_args()
    
    # Test script execution
    executor = ScriptExecutor(args.server, args.device)
    
    # Example script
    test_script = {
        "action": "launch",
        "path": "C:\\Windows\\System32\\notepad.exe",
        "process": "notepad.exe",
        "expected_duration": 10
    }
    
    result = executor.execute_script(test_script)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    input("\n执行完成，按回车键退出...")
    print(json.dumps(result, indent=2))
