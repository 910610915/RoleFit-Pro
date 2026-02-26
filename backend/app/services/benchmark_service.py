"""
Services for task execution and data analysis
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class TaskExecutor:
    """Execute benchmark tasks on devices"""
    
    @staticmethod
    async def execute_task(task_id: str, device_ids: List[str], test_config: dict) -> Dict[str, Any]:
        """
        Execute benchmark task on selected devices
        
        Args:
            task_id: Task ID
            device_ids: List of device IDs to run test on
            test_config: Test configuration
        
        Returns:
            Execution result
        """
        results = []
        
        for device_id in device_ids:
            # Simulate benchmark execution
            # In production, this would communicate with the agent
            result = {
                "task_id": task_id,
                "device_id": device_id,
                "test_status": "completed",
                "overall_score": 75.0 + (hash(device_id) % 25),  # Simulated score
                "cpu_score": 70.0 + (hash(device_id + "cpu") % 30),
                "gpu_score": 75.0 + (hash(device_id + "gpu") % 25),
                "memory_score": 80.0 + (hash(device_id + "mem") % 20),
                "disk_score": 85.0 + (hash(device_id + "disk") % 15),
                "duration_seconds": 300
            }
            results.append(result)
        
        return {
            "task_id": task_id,
            "total_devices": len(device_ids),
            "results": results,
            "completed_at": datetime.utcnow().isoformat()
        }


class PerformanceAnalyzer:
    """Analyze performance test results"""
    
    @staticmethod
    def calculate_overall_score(scores: Dict[str, float]) -> float:
        """Calculate weighted overall score"""
        weights = {
            "cpu": 0.30,
            "gpu": 0.35,
            "memory": 0.20,
            "disk": 0.15
        }
        
        overall = sum(
            scores.get(component, 0) * weight 
            for component, weight in weights.items()
        )
        
        return round(overall, 2)
    
    @staticmethod
    def identify_bottleneck(scores: Dict[str, float]) -> str:
        """Identify the main bottleneck"""
        min_score = float('inf')
        bottleneck = "NONE"
        
        for component, score in scores.items():
            if score < min_score:
                min_score = score
                bottleneck = component.upper()
        
        return bottleneck
    
    @staticmethod
    def generate_upgrade_suggestions(
        device_info: Dict[str, Any], 
        scores: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """Generate upgrade suggestions based on scores and device info"""
        suggestions = []
        
        if scores.get("cpu", 100) < 70:
            suggestions.append({
                "component": "CPU",
                "current": device_info.get("cpu_model", "Unknown"),
                "suggestion": "Consider upgrading to a higher performance CPU with more cores"
            })
        
        if scores.get("gpu", 100) < 70:
            suggestions.append({
                "component": "GPU",
                "current": device_info.get("gpu_model", "Unknown"),
                "suggestion": "Consider upgrading to a GPU with more VRAM for better graphics performance"
            })
        
        if scores.get("memory", 100) < 70:
            suggestions.append({
                "component": "Memory",
                "current": f"{device_info.get('ram_total_gb', 'Unknown')}GB",
                "suggestion": "Consider adding more RAM for better multitasking"
            })
        
        if scores.get("disk", 100) < 70:
            suggestions.append({
                "component": "Storage",
                "current": device_info.get("disk_type", "Unknown"),
                "suggestion": "Consider upgrading to NVMe SSD for faster read/write speeds"
            })
        
        return suggestions
    
    @staticmethod
    def check_standard_compliance(
        device_info: Dict[str, Any],
        standard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if device meets position standard"""
        compliance = {
            "is_compliant": True,
            "failed_checks": [],
            "passed_checks": []
        }
        
        # CPU check
        if standard.get("cpu_min_cores"):
            if device_info.get("cpu_cores", 0) < standard["cpu_min_cores"]:
                compliance["is_compliant"] = False
                compliance["failed_checks"].append(
                    f"CPU cores ({device_info.get('cpu_cores')}) below minimum ({standard['cpu_min_cores']})"
                )
            else:
                compliance["passed_checks"].append("CPU cores meet requirement")
        
        if standard.get("cpu_min_threads"):
            if device_info.get("cpu_threads", 0) < standard["cpu_min_threads"]:
                compliance["is_compliant"] = False
                compliance["failed_checks"].append(
                    f"CPU threads ({device_info.get('cpu_threads')}) below minimum ({standard['cpu_min_threads']})"
                )
        
        # RAM check
        if standard.get("ram_min_gb"):
            if device_info.get("ram_total_gb", 0) < standard["ram_min_gb"]:
                compliance["is_compliant"] = False
                compliance["failed_checks"].append(
                    f"RAM ({device_info.get('ram_total_gb')}GB) below minimum ({standard['ram_min_gb']}GB)"
                )
            else:
                compliance["passed_checks"].append("RAM meets requirement")
        
        # GPU check
        if standard.get("gpu_min_vram_mb"):
            if device_info.get("gpu_vram_mb", 0) < standard["gpu_min_vram_mb"]:
                compliance["is_compliant"] = False
                compliance["failed_checks"].append(
                    f"GPU VRAM ({device_info.get('gpu_vram_mb')}MB) below minimum ({standard['gpu_min_vram_mb']}MB)"
                )
            else:
                compliance["passed_checks"].append("GPU VRAM meets requirement")
        
        return compliance
    
    @staticmethod
    def calculate_trend(history: List[float], window: int = 5) -> str:
        """Calculate performance trend from history"""
        if len(history) < window:
            return "insufficient_data"
        
        recent = history[-window:]
        older = history[-window*2:-window] if len(history) >= window*2 else history[:window]
        
        if not older:
            return "stable"
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        change_percent = (recent_avg - older_avg) / older_avg * 100
        
        if change_percent > 5:
            return "improving"
        elif change_percent < -5:
            return "declining"
        else:
            return "stable"


class BenchmarkRunner:
    """Run various benchmark tests"""
    
    @staticmethod
    async def run_cpu_benchmark() -> Dict[str, Any]:
        """Run CPU benchmark"""
        # In production, this would use actual benchmark tools
        return {
            "score": 85.0,
            "single_core": 90.0,
            "multi_core": 82.0,
            "duration": 60
        }
    
    @staticmethod
    async def run_gpu_benchmark() -> Dict[str, Any]:
        """Run GPU benchmark"""
        return {
            "score": 88.0,
            "fps": 60.0,
            "render_time_ms": 16.5,
            "duration": 120
        }
    
    @staticmethod
    async def run_memory_benchmark() -> Dict[str, Any]:
        """Run memory benchmark"""
        return {
            "score": 80.0,
            "read_mbps": 25000,
            "write_mbps": 22000,
            "latency_ns": 65000,
            "duration": 30
        }
    
    @staticmethod
    async def run_disk_benchmark() -> Dict[str, Any]:
        """Run disk benchmark"""
        return {
            "score": 92.0,
            "read_mbps": 3500,
            "write_mbps": 2800,
            "iops": 450000,
            "duration": 60
        }
    
    @staticmethod
    async def run_full_benchmark() -> Dict[str, Any]:
        """Run full system benchmark"""
        cpu = await BenchmarkRunner.run_cpu_benchmark()
        gpu = await BenchmarkRunner.run_gpu_benchmark()
        memory = await BenchmarkRunner.run_memory_benchmark()
        disk = await BenchmarkRunner.run_disk_benchmark()
        
        # Calculate overall score
        weights = {"cpu": 0.30, "gpu": 0.35, "memory": 0.20, "disk": 0.15}
        overall = (
            cpu["score"] * weights["cpu"] +
            gpu["score"] * weights["gpu"] +
            memory["score"] * weights["memory"] +
            disk["score"] * weights["disk"]
        )
        
        return {
            "overall_score": round(overall, 2),
            "cpu_score": cpu["score"],
            "gpu_score": gpu["score"],
            "memory_score": memory["score"],
            "disk_score": disk["score"],
            "details": {
                "cpu": cpu,
                "gpu": gpu,
                "memory": memory,
                "disk": disk
            },
            "total_duration": cpu["duration"] + gpu["duration"] + memory["duration"] + disk["duration"]
        }
