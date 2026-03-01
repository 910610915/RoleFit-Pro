"""
Command Executor - Agent端命令接收和执行模块
负责从服务器接收命令并执行
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class CommandExecutor:
    """命令执行器"""

    # 支持的命令类型
    SUPPORTED_COMMANDS = [
        "start_benchmark",  # 开始基准测试
        "stop_benchmark",  # 停止基准测试
        "run_script",  # 运行脚本
        "collect_metrics",  # 立即采集指标
        "restart_agent",  # 重启Agent
        "update_config",  # 更新配置
        "install_software",  # 安装软件
        "uninstall_software",  # 卸载软件
    ]

    def __init__(self, device_id: str, server_url: str):
        self.device_id = device_id
        self.server_url = server_url.rstrip("/")
        self.current_command_id = None
        self.command_thread = None
        self.running = True

    def poll_commands(self) -> List[Dict[str, Any]]:
        """从服务器获取待执行的命令"""
        try:
            url = f"{self.server_url}/api/performance/commands/pending?device_id={self.device_id}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to poll commands: {e}")

        return []

    def acknowledge_command(self, command_id: str) -> bool:
        """确认接收命令"""
        try:
            url = f"{self.server_url}/api/performance/commands/{command_id}/acknowledge"
            response = requests.post(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to acknowledge command: {e}")
            return False

    def complete_command(
        self,
        command_id: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> bool:
        """命令执行完成"""
        try:
            url = f"{self.server_url}/api/performance/commands/{command_id}/complete"
            data = {}
            if result:
                data["result"] = json.dumps(result)
            if error:
                data["error_message"] = error

            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to complete command: {e}")
            return False

    def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个命令"""
        command_id = command.get("id")
        command_type = command.get("command_type")
        command_params = command.get("command_params")

        logger.info(f"Executing command: {command_type} (ID: {command_id})")

        # 解析参数
        params = {}
        if command_params:
            try:
                params = (
                    json.loads(command_params)
                    if isinstance(command_params, str)
                    else command_params
                )
            except:
                params = {}

        # 执行对应命令
        try:
            if command_type == "start_benchmark":
                result = self._execute_benchmark(params)
            elif command_type == "stop_benchmark":
                result = self._stop_benchmark(params)
            elif command_type == "run_script":
                result = self._run_script(params)
            elif command_type == "collect_metrics":
                result = self._collect_now()
            elif command_type == "restart_agent":
                result = {"status": "restarting"}
                self.running = False
            elif command_type == "update_config":
                result = self._update_config(params)
            else:
                result = {"error": f"Unknown command type: {command_type}"}

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"error": str(e)}

    def _execute_benchmark(self, params: Dict) -> Dict[str, Any]:
        """执行基准测试"""
        software = params.get("software_code", "blender")
        benchmark_type = params.get("benchmark_type", "render")

        logger.info(f"Starting benchmark: {software} - {benchmark_type}")

        # 根据软件类型选择不同的基准测试
        if software == "blender":
            return self._run_blender_benchmark(params)
        elif software == "maya":
            return self._run_maya_benchmark(params)
        elif software == "unreal":
            return self._run_unreal_benchmark(params)
        else:
            return {"error": f"Unsupported software: {software}"}

    def _run_blender_benchmark(self, params: Dict) -> Dict[str, Any]:
        """运行 Blender 基准测试"""
        try:
            # 调用 blender_benchmark.py 脚本
            import blender_benchmark

            benchmark = blender_benchmark.BlenderBenchmark(self.device_id)
            results = benchmark.run_benchmark(
                scene_file=params.get("scene_file"), samples=params.get("samples", 128)
            )

            # 上报结果
            benchmark.submit_results(results)

            return results
        except Exception as e:
            return {"error": f"Blender benchmark failed: {e}"}

    def _run_maya_benchmark(self, params: Dict) -> Dict[str, Any]:
        """运行 Maya 基准测试"""
        # TODO: 实现 Maya 基准测试
        return {"error": "Maya benchmark not implemented yet"}

    def _run_unreal_benchmark(self, params: Dict) -> Dict[str, Any]:
        """运行 Unreal Engine 基准测试"""
        # TODO: 实现 Unreal 基准测试
        return {"error": "Unreal benchmark not implemented yet"}

    def _stop_benchmark(self, params: Dict) -> Dict[str, Any]:
        """停止正在运行的基准测试"""
        # 查找并终止 Blender 进程
        try:
            for proc in subprocess.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "blender" in proc.info["name"].lower():
                        proc.kill()
                        logger.info(f"Killed process: {proc.info['pid']}")
                except:
                    pass
            return {"status": "stopped"}
        except Exception as e:
            return {"error": str(e)}

    def _run_script(self, params: Dict) -> Dict[str, Any]:
        """运行自定义脚本"""
        script_path = params.get("script_path")
        if not script_path:
            return {"error": "script_path is required"}

        if not os.path.exists(script_path):
            return {"error": f"Script not found: {script_path}"}

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 300),
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Script execution timeout"}
        except Exception as e:
            return {"error": str(e)}

    def _collect_now(self, params: Dict) -> Dict[str, Any]:
        """立即采集一次指标"""
        try:
            # 采集指标并上报
            from hardware_monitor import PerformanceMonitor

            monitor = PerformanceMonitor(self.device_id)
            metrics = monitor.collect_metrics()
            monitor.send_metrics(metrics)

            return {"status": "collected", "metrics": metrics}
        except Exception as e:
            return {"error": str(e)}

    def _update_config(self, params: Dict) -> Dict[str, Any]:
        """更新Agent配置"""
        try:
            # 更新配置到文件
            config_file = "agent_config.json"

            # 读取现有配置
            config = {}
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)

            # 更新配置
            config.update(params)

            # 写入配置
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            return {"status": "updated", "config": config}
        except Exception as e:
            return {"error": str(e)}

    def process_commands(self):
        """处理待执行的命令"""
        commands = self.poll_commands()

        for command in commands:
            command_id = command.get("id")

            # 跳过正在执行的命令
            if command.get("status") in ["executing", "completed"]:
                continue

            # 确认接收命令
            if not self.acknowledge_command(command_id):
                logger.warning(f"Failed to acknowledge command {command_id}")
                continue

            # 执行命令
            result = self.execute_command(command)

            # 上报结果
            if "error" in result:
                self.complete_command(command_id, error=result["error"])
            else:
                self.complete_command(command_id, result=result)

    def run(self):
        """命令处理循环"""
        logger.info("Command executor started")

        while self.running:
            try:
                self.process_commands()
                time.sleep(5)  # 每5秒检查一次命令
            except Exception as e:
                logger.error(f"Error in command processor: {e}")
                time.sleep(10)

        logger.info("Command executor stopped")

    def stop(self):
        """停止命令处理"""
        self.running = False


# Integration helper - 在现有 agent 中添加命令处理
def add_command_support(agent):
    """为现有Agent添加命令支持"""
    executor = CommandExecutor(agent.device_id, agent.server_url)

    # 添加命令执行器到agent
    agent.command_executor = executor

    # 修改主循环以处理命令
    original_run = agent.run

    def new_run():
        # 启动命令处理线程
        command_thread = threading.Thread(target=executor.run, daemon=True)
        command_thread.start()

        # 调用原始run方法
        return original_run()

    agent.run = new_run

    return agent
