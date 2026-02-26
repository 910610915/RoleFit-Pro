# Benchmark Tests for Hardware Benchmark Agent
# Built-in benchmark tests for CPU, GPU, Memory, and Disk

import os
import time
import json
import logging
import subprocess
import threading
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CPUBenchmark:
    """CPU Benchmark Tests"""
    
    @staticmethod
    def run_simple_cpu_test(duration: int = 30) -> Dict[str, Any]:
        """
        Run a simple CPU stress test
        Calculates prime numbers to stress CPU
        """
        result = {
            "test_name": "CPU Benchmark",
            "duration_seconds": duration,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "score": 0,
            "details": {}
        }
        
        try:
            # Simple prime calculation test
            prime_count = 0
            start = time.time()
            
            while time.time() - start < duration:
                # Calculate primes up to 10000
                for num in range(2, 10000):
                    is_prime = True
                    for i in range(2, int(num ** 0.5) + 1):
                        if num % i == 0:
                            is_prime = False
                            break
                    if is_prime:
                        prime_count += 1
                
                # Check CPU usage during test
                cpu_percent = psutil.cpu_percent(interval=0.1)
                result["details"]["cpu_usage_percent"] = max(
                    result["details"].get("cpu_usage_percent", 0), 
                    cpu_percent
                )
            
            result["success"] = True
            result["score"] = prime_count
            result["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"CPU benchmark error: {e}")
        
        return result
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information"""
        cpu_freq = psutil.cpu_freq()
        return {
            "cpu_model": psutil.cpu_stats(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "max_frequency_mhz": cpu_freq.max if cpu_freq else 0,
            "current_frequency_mhz": cpu_freq.current if cpu_freq else 0,
        }


class MemoryBenchmark:
    """Memory Benchmark Tests"""
    
    @staticmethod
    def run_memory_test(duration: int = 30) -> Dict[str, Any]:
        """
        Run memory read/write test
        """
        result = {
            "test_name": "Memory Benchmark",
            "duration_seconds": duration,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "score": 0,
            "details": {}
        }
        
        try:
            # Memory test: allocate and access memory
            mem = psutil.virtual_memory()
            test_size_mb = min(1024, int(mem.available / (1024 * 1024) * 0.5))  # Use 50% of available
            
            start = time.time()
            operations = 0
            
            # Allocate memory
            data = bytearray(test_size_mb * 1024 * 1024)
            
            while time.time() - start < duration:
                # Write to memory
                for i in range(0, len(data), 4096):
                    data[i] = (i % 256)
                
                # Read from memory
                checksum = sum(data[::4096])
                
                operations += 1
                
                # Monitor memory usage
                mem = psutil.virtual_memory()
                result["details"]["memory_usage_percent"] = max(
                    result["details"].get("memory_usage_percent", 0),
                    mem.percent
                )
            
            result["success"] = True
            result["score"] = operations * test_size_mb
            result["details"]["test_size_mb"] = test_size_mb
            result["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Memory benchmark error: {e}")
        
        return result


class DiskBenchmark:
    """Disk Benchmark Tests"""
    
    @staticmethod
    def run_disk_test(duration: int = 30, test_file: str = None) -> Dict[str, Any]:
        """
        Run disk read/write benchmark
        """
        result = {
            "test_name": "Disk Benchmark",
            "duration_seconds": duration,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "score": 0,
            "details": {}
        }
        
        # Use temp directory if no test file specified
        if not test_file:
            test_file = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), 
                                      f"benchmark_{int(time.time())}.tmp")
        
        try:
            # Test parameters
            chunk_size = 1024 * 1024  # 1MB chunks
            test_size_mb = 100  # 100MB test file
            
            # Write test
            write_speed_mbps = DiskBenchmark._test_write(test_file, chunk_size, test_size_mb)
            
            # Read test
            read_speed_mbps = DiskBenchmark._test_read(test_file, chunk_size, test_size_mb)
            
            # Clean up
            try:
                os.remove(test_file)
            except:
                pass
            
            result["success"] = True
            result["score"] = int(read_speed_mbps)  # Use read speed as score
            result["details"] = {
                "write_speed_mbps": write_speed_mbps,
                "read_speed_mbps": read_speed_mbps,
                "test_file": test_file,
                "test_size_mb": test_size_mb
            }
            result["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Disk benchmark error: {e}")
        
        return result
    
    @staticmethod
    def _test_write(test_file: str, chunk_size: int, size_mb: int) -> float:
        """Test disk write speed"""
        data = b'x' * chunk_size
        chunks = size_mb * 1024 * 1024 // chunk_size
        
        start = time.time()
        
        with open(test_file, 'wb') as f:
            for _ in range(chunks):
                f.write(data)
            f.flush()
            os.fsync(f.fileno())
        
        elapsed = time.time() - start
        return (size_mb / elapsed) if elapsed > 0 else 0
    
    @staticmethod
    def _test_read(test_file: str, chunk_size: int, size_mb: int) -> float:
        """Test disk read speed"""
        chunks = size_mb * 1024 * 1024 // chunk_size
        
        start = time.time()
        
        with open(test_file, 'rb') as f:
            for _ in range(chunks):
                f.read(chunk_size)
        
        elapsed = time.time() - start
        return (size_mb / elapsed) if elapsed > 0 else 0


class GPUBenchmark:
    """GPU Benchmark Tests"""
    
    @staticmethod
    def run_simple_gpu_test(duration: int = 30) -> Dict[str, Any]:
        """
        Run simple GPU test (requires NVIDIA GPU)
        """
        result = {
            "test_name": "GPU Benchmark",
            "duration_seconds": duration,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "score": 0,
            "details": {}
        }
        
        try:
            # Try to use NVIDIA GPU if available
            import wmi
            wmi_obj = wmi.WMI()
            
            gpu_found = False
            for gpu in wmi_obj.Win32_VideoController():
                gpu_name = gpu.Name.lower() if gpu.Name else ""
                if "nvidia" in gpu_name or "geforce" in gpu_name:
                    gpu_found = True
                    result["details"]["gpu_name"] = gpu.Name
                    
                    # Try to get GPU info via nvidia-smi
                    try:
                        output = subprocess.check_output(
                            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", 
                             "--format=csv,noheader,nounits"],
                            stderr=subprocess.STDOUT,
                            timeout=5
                        )
                        lines = output.decode('utf-8').strip().split('\n')
                        if lines:
                            parts = lines[0].split(',')
                            result["details"]["gpu_utilization_percent"] = float(parts[0].strip())
                            result["details"]["gpu_memory_used_mb"] = float(parts[1].strip())
                            result["details"]["gpu_memory_total_mb"] = float(parts[2].strip())
                    except:
                        pass
                    
                    break
            
            if not gpu_found:
                result["details"]["message"] = "No NVIDIA GPU found, skipping GPU test"
            
            result["success"] = True
            result["score"] = result["details"].get("gpu_utilization_percent", 0)
            result["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"GPU benchmark error: {e}")
        
        return result


class BenchmarkRunner:
    """Main benchmark runner"""
    
    TESTS = {
        "cpu": CPUBenchmark.run_simple_cpu_test,
        "memory": MemoryBenchmark.run_memory_test,
        "disk": DiskBenchmark.run_disk_test,
        "gpu": GPUBenchmark.run_simple_gpu_test,
        "full": None  # Will run all tests
    }
    
    @staticmethod
    def run_benchmark(test_type: str = "full", duration: int = 30) -> Dict[str, Any]:
        """
        Run benchmark tests
        
        Args:
            test_type: "cpu", "memory", "disk", "gpu", or "full"
            duration: Duration of each test in seconds
        """
        result = {
            "test_type": test_type,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "tests": {}
        }
        
        if test_type == "full":
            # Run all tests
            for test_name, test_func in BenchmarkRunner.TESTS.items():
                if test_name != "full" and test_func:
                    logger.info(f"Running {test_name} benchmark...")
                    result["tests"][test_name] = test_func(duration)
        else:
            # Run specific test
            test_func = BenchmarkRunner.TESTS.get(test_type)
            if test_func:
                result["tests"][test_type] = test_func(duration)
            else:
                result["error"] = f"Unknown test type: {test_type}"
        
        result["end_time"] = datetime.utcnow().isoformat()
        return result


# Example usage
if __name__ == "__main__":
    # Test CPU benchmark
    print("Running CPU benchmark...")
    result = CPUBenchmark.run_simple_cpu_test(10)
    print(json.dumps(result, indent=2))
    
    # Test memory benchmark
    print("\nRunning Memory benchmark...")
    result = MemoryBenchmark.run_memory_test(10)
    print(json.dumps(result, indent=2))
    
    # Test disk benchmark
    print("\nRunning Disk benchmark...")
    result = DiskBenchmark.run_disk_test(10)
    print(json.dumps(result, indent=2))
