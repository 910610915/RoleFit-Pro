"""
Prometheus Exporter Agent
基于 prometheus_client 的替代方案，用于没有 windows_exporter 的环境

功能:
- 采集 CPU、内存、磁盘、网络指标
- 通过 HTTP 暴露 /metrics 端点供 Prometheus 抓取

安装依赖:
    pip install prometheus-client psutil

运行:
    python prometheus_exporter_agent.py

Windows 服务安装:
    pip install pywin32
    python prometheus_exporter_agent.py --install-service
"""

import os
import sys
import time
import logging
import platform
import subprocess
from typing import Optional
from threading import Thread

# Prometheus client
from prometheus_client import start_http_server, Gauge, Counter, Info, REGISTRY

# 系统监控
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil 未安装，将使用有限指标")

# Windows 特定
if sys.platform == "win32":
    try:
        import win32service
        import win32serviceutil
        import win32con
        import pythoncom

        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("prometheus_exporter.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ============================================
# Prometheus 指标定义
# ============================================

# CPU 指标
CPU_PERCENT = Gauge("windows_cpu_percent", "CPU usage percent")
CPU_FREQUENCY = Gauge("windows_cpu_frequency", "CPU frequency in MHz")

# 内存指标
MEMORY_PERCENT = Gauge("windows_memory_percent", "Memory usage percent")
MEMORY_AVAILABLE = Gauge("windows_memory_available_bytes", "Available memory in bytes")
MEMORY_USED = Gauge("windows_memory_used_bytes", "Used memory in bytes")

# 磁盘指标
DISK_READ_BYTES = Counter("windows_disk_read_bytes_total", "Total disk read bytes")
DISK_WRITE_BYTES = Counter("windows_disk_write_bytes_total", "Total disk write bytes")

# 网络指标
NETWORK_SENT_BYTES = Counter(
    "windows_network_sent_bytes_total", "Total network sent bytes"
)
NETWORK_RECV_BYTES = Counter(
    "windows_network_recv_bytes_total", "Total network received bytes"
)

# GPU 指标 (如果有)
GPU_PERCENT = Gauge("windows_gpu_percent", "GPU usage percent")
GPU_TEMPERATURE = Gauge("windows_gpu_temperature_celsius", "GPU temperature in Celsius")
GPU_MEMORY_USED = Gauge("windows_gpu_memory_used_bytes", "GPU memory used in bytes")
GPU_MEMORY_TOTAL = Gauge("windows_gpu_memory_total_bytes", "GPU memory total in bytes")

# 系统信息
SYSTEM_INFO = Info("windows_system", "System information")

# 上一次采集的数据（用于计算速率）
_last_disk_read = 0
_last_disk_write = 0
_last_net_sent = 0
_last_net_recv = 0
_last_timestamp = time.time()


def get_cpu_metrics():
    """获取 CPU 指标"""
    if not PSUTIL_AVAILABLE:
        return

    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        CPU_PERCENT.set(cpu_percent)

        # CPU 频率 (如果可用)
        try:
            freq = psutil.cpu_freq()
            if freq:
                CPU_FREQUENCY.set(freq.current)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"获取 CPU 指标失败: {e}")


def get_memory_metrics():
    """获取内存指标"""
    if not PSUTIL_AVAILABLE:
        return

    try:
        mem = psutil.virtual_memory()
        MEMORY_PERCENT.set(mem.percent)
        MEMORY_AVAILABLE.set(mem.available)
        MEMORY_USED.set(mem.used)
    except Exception as e:
        logger.error(f"获取内存指标失败: {e}")


def get_disk_metrics():
    """获取磁盘 IO 指标"""
    global _last_disk_read, _last_disk_write, _last_timestamp

    if not PSUTIL_AVAILABLE:
        return

    try:
        disk_io = psutil.disk_io_counters()
        if disk_io:
            current_read = disk_io.read_bytes
            current_write = disk_io.write_bytes

            # 计算增量
            time_diff = time.time() - _last_timestamp
            if time_diff > 0:
                read_rate = (current_read - _last_disk_read) / time_diff
                write_rate = (current_write - _last_disk_write) / time_diff

                # 只记录正增量（避免重启后计数器归零）
                if read_rate >= 0:
                    DISK_READ_BYTES.inc(read_rate)
                if write_rate >= 0:
                    DISK_WRITE_BYTES.inc(write_rate)

            _last_disk_read = current_read
            _last_disk_write = current_write
            _last_timestamp = time.time()
    except Exception as e:
        logger.error(f"获取磁盘指标失败: {e}")


def get_network_metrics():
    """获取网络指标"""
    global _last_net_sent, _last_net_recv, _last_timestamp

    if not PSUTIL_AVAILABLE:
        return

    try:
        net_io = psutil.net_io_counters()
        if net_io:
            current_sent = net_io.bytes_sent
            current_recv = net_io.bytes_recv

            time_diff = time.time() - _last_timestamp
            if time_diff > 0:
                sent_rate = (current_sent - _last_net_sent) / time_diff
                recv_rate = (current_recv - _last_net_recv) / time_diff

                if sent_rate >= 0:
                    NETWORK_SENT_BYTES.inc(sent_rate)
                if recv_rate >= 0:
                    NETWORK_RECV_BYTES.inc(recv_rate)

            _last_net_sent = current_sent
            _last_net_recv = current_recv
    except Exception as e:
        logger.error(f"获取网络指标失败: {e}")


def get_gpu_metrics():
    """获取 GPU 指标（通过 nvidia-smi）"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 4:
                gpu_util = float(parts[0].strip())
                gpu_temp = float(parts[1].strip())
                gpu_mem_used = float(parts[2].strip()) * 1024 * 1024  # MiB -> bytes
                gpu_mem_total = float(parts[3].strip()) * 1024 * 1024

                GPU_PERCENT.set(gpu_util)
                GPU_TEMPERATURE.set(gpu_temp)
                GPU_MEMORY_USED.set(gpu_mem_used)
                GPU_MEMORY_TOTAL.set(gpu_mem_total)
    except FileNotFoundError:
        logger.debug("nvidia-smi 未找到，跳过 GPU 指标")
    except Exception as e:
        logger.error(f"获取 GPU 指标失败: {e}")


def get_system_info():
    """获取系统信息"""
    try:
        SYSTEM_INFO.info(
            {
                "hostname": platform.node(),
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
            }
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")


def collect_metrics():
    """采集所有指标"""
    get_system_info()
    get_cpu_metrics()
    get_memory_metrics()
    get_disk_metrics()
    get_network_metrics()
    get_gpu_metrics()


def collection_loop(interval: int = 15):
    """指标采集循环"""
    global _last_timestamp
    _last_timestamp = time.time()

    while True:
        try:
            collect_metrics()
            time.sleep(interval)
        except Exception as e:
            logger.error(f"采集循环错误: {e}")
            time.sleep(interval)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Prometheus Exporter Agent")
    parser.add_argument("--port", type=int, default=9100, help="HTTP 端口 (默认: 9100)")
    parser.add_argument(
        "--interval", type=int, default=15, help="采集间隔秒数 (默认: 15)"
    )
    parser.add_argument(
        "--install-service", action="store_true", help="安装为 Windows 服务"
    )
    args = parser.parse_args()

    logger.info(f"启动 Prometheus Exporter Agent...")
    logger.info(f"  端口: {args.port}")
    logger.info(f"  采集间隔: {args.interval} 秒")
    logger.info(f"  指标端点: http://localhost:{args.port}/metrics")

    # 检查 psutil
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil 未安装，CPU/内存/磁盘/网络指标将不可用")
        logger.warning("安装方式: pip install psutil")

    # 安装为 Windows 服务
    if args.install_service and sys.platform == "win32":
        if not WIN32_AVAILABLE:
            logger.error("pywin32 未安装，无法安装服务")
            logger.error("安装方式: pip install pywin32")
            return

        logger.info("正在安装为 Windows 服务...")
        try:
            pythoncom.CoInitializeEx(0, pythoncom.COINIT_MULTITHREADED)
            import win32serviceutil

            win32serviceutil.InstallService(
                pythoncom.GetCurrentProcessId(),
                "PrometheusExporterAgent",
                "Prometheus Exporter Agent",
                startType=win32service.SERVICE_AUTO_START,
            )
            logger.info("服务安装成功")
            return
        except Exception as e:
            logger.error(f"服务安装失败: {e}")
            return

    # 启动 HTTP 服务器（Prometheus 抓取端点）
    start_http_server(args.port)
    logger.info(f"HTTP 服务器已启动，监听端口 {args.port}")

    # 启动采集线程
    collector_thread = Thread(
        target=collection_loop, args=(args.interval,), daemon=True
    )
    collector_thread.start()
    logger.info(f"采集线程已启动，间隔 {args.interval} 秒")

    logger.info("Prometheus Exporter Agent 运行中...")
    logger.info("按 Ctrl+C 停止")

    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在退出...")
        sys.exit(0)


if __name__ == "__main__":
    main()
