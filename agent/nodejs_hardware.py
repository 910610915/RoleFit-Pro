"""
Node.js Hardware Info Wrapper
使用 Node.js + systeminformation 获取准确的硬件信息
"""

import subprocess
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Node.js 脚本路径
NODE_SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "nodejs", "hardware_info")
NODE_SCRIPT = os.path.join(NODE_SCRIPT_DIR, "hardware_info.js")
NODE_EXE = "node"  # 使用系统中的 node 命令


def is_node_available() -> bool:
    """检查 Node.js 是否可用"""
    try:
        result = subprocess.run(
            [NODE_EXE, "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def run_node_script(args: list = None) -> Optional[Dict[str, Any]]:
    """运行 Node.js 脚本并返回结果"""
    if args is None:
        args = []

    try:
        cmd = [NODE_EXE, NODE_SCRIPT] + args
        # logger.debug(f"Running Node.js command: {' '.join(cmd)}")
        
        # Increase timeout to 60 seconds for slower machines
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=NODE_SCRIPT_DIR,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            logger.error(f"Node.js script error (code {result.returncode}): {result.stderr}")
            # Try to parse stdout even if return code is non-zero, sometimes partial json is printed
            if not result.stdout.strip():
                return None
        
        if not result.stdout:
            logger.error("Node.js script returned empty stdout")
            return None

        # 修复Windows路径中的反斜杠问题
        # Windows路径如 C:\Users 会导致JSON解析失败，因为\U不是有效转义
        stdout = result.stdout
        # 将反斜杠替换为正斜杠（Windows路径标准化）
        stdout = stdout.replace("\\\\", "/").replace("\\", "/")

        return json.loads(stdout)
    except subprocess.TimeoutExpired:
        logger.error("Node.js script timeout")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Node.js output: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to run Node.js script: {e}")
        return None


def get_hardware_info() -> Dict[str, Any]:
    """
    获取硬件信息
    使用 Node.js + systeminformation 库
    """
    if not is_node_available():
        raise RuntimeError(
            "Node.js is not available. Please install Node.js from https://nodejs.org/"
        )

    result = run_node_script(["info"])

    if not result or not result.get("success"):
        error_msg = result.get("error", "Unknown error") if result else "No response"
        raise RuntimeError(f"Failed to get hardware info: {error_msg}")

    data = result.get("data", {})

    # 转换为兼容格式
    info = {}

    # CPU
    cpu = data.get("cpu", {})
    info["cpu_model"] = cpu.get("brand", "Unknown")
    info["cpu_cores"] = cpu.get("cores", 0)
    info["cpu_threads"] = cpu.get("cores", 0)
    info["cpu_base_clock"] = cpu.get("speedMax", cpu.get("speed", 0))  # MHz
    info["cpu_current_speed"] = cpu.get("currentSpeed", 0)

    # Memory
    mem = data.get("memory", {})
    info["ram_total_gb"] = mem.get("total_gb", 0)
    info["ram_frequency"] = None  # systeminformation 不直接提供频率
    info["all_memory"] = mem.get("layout", [])

    # GPU
    gpus = data.get("graphics", {}).get("gpus", [])
    if gpus:
        primary_gpu = gpus[0]
        info["gpu_model"] = primary_gpu.get("name", "Unknown")
        info["gpu_vram_mb"] = primary_gpu.get("vram_mb", 0)
        info["gpu_driver_version"] = primary_gpu.get("driver_version")
        info["all_gpus"] = gpus

    # Disk
    disks = data.get("disk", {}).get("layout", [])
    if disks:
        primary_disk = disks[0]
        info["disk_model"] = primary_disk.get("name", "Unknown")
        info["disk_capacity_tb"] = primary_disk.get("size_tb", 0)
        info["disk_type"] = primary_disk.get("type", "Unknown")
        info["all_disks"] = disks

    # OS
    os_info = data.get("os", {})
    info["os_name"] = os_info.get("platform", "Windows")
    info["os_version"] = os_info.get("release", "")
    info["os_build"] = os_info.get("build", "")
    info["hostname"] = os_info.get("hostname", "")

    # Network
    network = data.get("network", [])
    if network:
        info["mac_address"] = network[0].get("mac", "")
        info["ip_address"] = network[0].get("ip4", "")

    return info


def get_realtime_metrics() -> Dict[str, Any]:
    """
    获取实时性能指标
    使用 Node.js + systeminformation 库
    """
    if not is_node_available():
        raise RuntimeError(
            "Node.js is not available. Please install Node.js from https://nodejs.org/"
        )

    result = run_node_script(["metrics"])

    if not result or not result.get("success"):
        # Log the raw output if failed
        if result and "error" in result:
            logger.error(f"Node.js script failed: {result.get('error')}")
        error_msg = result.get("error", "Unknown error") if result else "No response"
        raise RuntimeError(f"Failed to get realtime metrics: {error_msg}")

    data = result.get("data", {})

    # Memory
    mem_data = data.get("memory", {})
    mem_total = mem_data.get("total", 0) or 0
    mem_used = mem_data.get("used", 0) or 0
    mem_avail = mem_data.get("available", 0) or 0
    
    # Calculate percent if missing
    mem_percent = mem_data.get("percent")
    if mem_percent is None and mem_total > 0:
        mem_percent = round((mem_used / mem_total) * 100, 2)
        
    metrics = {
        "cpu_percent": data.get("cpu", {}).get("percent", 0),
        "cpu_frequency_mhz": data.get("cpu", {}).get("speed", 0),
        "memory_percent": mem_percent,
        "memory_used_mb": round(mem_used / 1024 / 1024, 2),
        "memory_available_mb": round(mem_avail / 1024 / 1024, 2),
        "gpu_percent": data.get("gpu", {}).get("percent"),
        "gpu_temperature": data.get("gpu", {}).get("temperature"),
        "gpu_memory_used_mb": data.get("gpu", {}).get("memory_used_mb"),
        "gpu_memory_total_mb": data.get("gpu", {}).get("memory_total_mb"),
        "disk_read_bytes": data.get("disk", {}).get("read_bytes", 0),
        "disk_write_bytes": data.get("disk", {}).get("write_bytes", 0),
        "disk_io_details": data.get("disk", {}).get("details", []),
        "network_sent_bytes": data.get("network", {}).get("tx_bytes", 0),
        "network_recv_bytes": data.get("network", {}).get("rx_bytes", 0),
        "top_processes": data.get("top_processes", []),
    }

    return metrics


# 测试
if __name__ == "__main__":
    print("Testing Node.js Hardware Info...")
    print(f"Node.js available: {is_node_available()}")
    print()

    if is_node_available():
        print("Getting hardware info...")
        info = get_hardware_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
        print()

        print("Getting realtime metrics...")
        metrics = get_realtime_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        print("ERROR: Please install Node.js to use systeminformation")
