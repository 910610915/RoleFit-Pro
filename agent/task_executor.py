"""
Task Executor - Agent端任务接收和执行模块
负责从服务器获取测试任务并执行
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


class TaskExecutor:
    """测试任务执行器"""

    def __init__(self, device_id: str, server_url: str, api_key: Optional[str] = None):
        self.device_id = device_id
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.current_task_id = None
        self.task_thread = None
        self.running = True
        self._task_lock = threading.Lock()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def poll_pending_tasks(self) -> Optional[Dict[str, Any]]:
        """从服务器获取待执行的任务"""
        try:
            url = f"{self.server_url}/api/tasks/pending?device_id={self.device_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                data = response.json()
                # 处理列表响应
                if isinstance(data, list) and data:
                    return data[0]
                # 处理分页响应
                elif isinstance(data, dict) and data.get("items"):
                    items = data["items"]
                    if items:
                        return items[0]
        except Exception as e:
            logger.error(f"Failed to poll tasks: {e}")

        return None

    def mark_task_running(self, task_id: str, device_ids: List[str]) -> bool:
        """通知服务器任务开始执行"""
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/execute"
            data = {"device_ids": device_ids}
            response = requests.post(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to mark task running: {e}")
            return False

    def mark_task_complete(self, task_id: str, task_status: str = "completed") -> bool:
        """通知服务器任务完成"""
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/complete"
            data = {"task_status": task_status}
            response = requests.post(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to mark task complete: {e}")
            return False

    def report_task_error(self, task_id: str, error_message: str) -> bool:
        """上报任务执行错误"""
        try:
            url = f"{self.server_url}/api/tasks/{task_id}/software_error"
            data = {
                "error_type": "task_execution",
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": self.device_id,
            }
            response = requests.post(
                url, json=data, headers=self._get_headers(), timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to report task error: {e}")
            return False

    def submit_test_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """上报测试结果，返回结果ID或错误信息"""
        try:
            url = f"{self.server_url}/api/results"
            response = requests.post(
                url, json=result_data, headers=self._get_headers(), timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                result_id = result.get("id")
                logger.info(f"Test result submitted successfully: {result_id}")
                return {"success": True, "result_id": result_id, "data": result}
            else:
                error_msg = (
                    f"Failed to submit result: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Submit result timeout"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to submit test result: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试任务"""
        task_id = task.get("id")
        task_type = task.get("task_type", "benchmark")
        task_name = task.get("task_name", "Unknown Task")

        logger.info(f"Starting task execution: {task_name} (type: {task_type})")

        # 通知任务开始
        target_devices = task.get("target_device_ids", [])
        if isinstance(target_devices, str):
            try:
                target_devices = json.loads(target_devices)
            except:
                target_devices = [self.device_id]
        elif not target_devices:
            target_devices = [self.device_id]

        if not self.mark_task_running(task_id, target_devices):
            logger.warning(f"Failed to mark task {task_id} as running")

        self.current_task_id = task_id
        start_time = datetime.utcnow()

        try:
            # 根据任务类型执行
            if task_type == "benchmark":
                result = self._execute_benchmark_task(task)
            elif task_type == "simulation":
                result = self._execute_simulation_task(task)
            elif task_type == "full":
                result = self._execute_full_task(task)
            elif task_type == "custom":
                result = self._execute_custom_task(task)
            else:
                result = {"error": f"Unknown task type: {task_type}"}

            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())

            # 构建结果数据
            result_data = {
                "task_id": task_id,
                "device_id": self.device_id,
                "test_type": task_type,
                "test_status": "passed" if "error" not in result else "failed",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
            }

            # 添加分数（如果有）
            if "score" in result:
                result_data["overall_score"] = result.get("score")
                result_data["cpu_score"] = result.get("cpu_score")
                result_data["gpu_score"] = result.get("gpu_score")
                result_data["memory_score"] = result.get("memory_score")
                result_data["disk_score"] = result.get("disk_score")

            # 添加瓶颈分析
            if "bottleneck" in result:
                result_data["bottleneck_type"] = result.get("bottleneck")

            # 上报结果并检查是否成功
            submit_result = self.submit_test_result(result_data)

            # 如果结果提交失败，标记任务为部分完成但记录错误
            if not submit_result.get("success"):
                error_msg = submit_result.get(
                    "error", "Unknown error submitting result"
                )
                logger.error(f"Failed to submit test result: {error_msg}")
                # 将错误信息添加到 result 中
                result["submit_error"] = error_msg
                result["submit_result_id"] = submit_result.get("result_id")

                # 即使提交失败也标记任务完成，但记录状态
                task_status = "completed" if "error" not in result else "failed"
                self.mark_task_complete(task_id, task_status)
            else:
                # 标记任务完成
                task_status = "failed" if "error" in result else "completed"
                self.mark_task_complete(task_id, task_status)

            logger.info(f"Task {task_id} completed with status: {task_status}")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task_id} execution failed: {error_msg}")

            # 上报错误
            self.report_task_error(task_id, error_msg)
            self.mark_task_complete(task_id, "failed")

            return {"error": error_msg}

        finally:
            self.current_task_id = None

    def _execute_benchmark_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行基础性能测试任务"""
        logger.info("Executing benchmark task - CPU/GPU/内存/磁盘基础测试")

        try:
            # 调用 Node.js 硬件信息采集获取即时指标
            from nodejs_hardware import get_hardware_info

            hardware_info = get_hardware_info()

            # 简单的基准测试：采集基线指标
            time.sleep(2)  # 等待系统稳定

            # 获取运行时指标
            from nodejs_hardware import get_realtime_metrics

            metrics = get_realtime_metrics()

            # 计算简单分数（基于硬件规格）
            cpu_score = self._calculate_cpu_score(hardware_info)
            gpu_score = self._calculate_gpu_score(hardware_info)
            memory_score = self._calculate_memory_score(hardware_info)
            disk_score = self._calculate_disk_score(hardware_info)
            overall_score = (cpu_score + gpu_score + memory_score + disk_score) / 4

            # 确定瓶颈
            scores = {
                "cpu": cpu_score,
                "gpu": gpu_score,
                "memory": memory_score,
                "disk": disk_score,
            }
            bottleneck = min(scores, key=scores.get)

            return {
                "score": overall_score,
                "cpu_score": cpu_score,
                "gpu_score": gpu_score,
                "memory_score": memory_score,
                "disk_score": disk_score,
                "bottleneck": bottleneck,
                "hardware_info": hardware_info,
                "metrics": metrics,
            }

        except Exception as e:
            return {"error": f"Benchmark task failed: {str(e)}"}

    def _execute_simulation_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行模拟游戏工作负载任务"""
        logger.info("Executing simulation task - 模拟游戏工作负载")

        try:
            # 尝试运行 Blender 基准测试作为模拟
            import blender_benchmark

            benchmark = blender_benchmark.BlenderBenchmark(self.device_id)
            results = benchmark.run_benchmark(samples=64)  # 减少样本数加快测试

            return {
                "score": results.get("score", 0),
                "cpu_score": results.get("score_cpu", 0),
                "gpu_score": results.get("score_gpu", 0),
                "memory_score": results.get("avg_memory_mb", 0) / 10,
                "disk_score": 50,  # 默认值
                "bottleneck": results.get("bottleneck_type", "unknown"),
            }

        except ImportError:
            # Blender 不可用，回退到基础测试
            logger.warning("Blender not available, falling back to basic benchmark")
            return self._execute_benchmark_task(task)
        except Exception as e:
            return {"error": f"Simulation task failed: {str(e)}"}

    def _execute_full_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整测试套件"""
        logger.info("Executing full task - 完整测试套件")

        try:
            # 运行完整的 Blender 基准测试
            import blender_benchmark

            benchmark = blender_benchmark.BlenderBenchmark(self.device_id)
            results = benchmark.run_benchmark(samples=128)

            return {
                "score": results.get("score", 0),
                "cpu_score": results.get("score_cpu", 0),
                "gpu_score": results.get("score_gpu", 0),
                "memory_score": results.get("avg_memory_mb", 0) / 10,
                "disk_score": 50,
                "bottleneck": results.get("bottleneck_type", "unknown"),
            }

        except ImportError:
            logger.warning("Blender not available, falling back to basic benchmark")
            return self._execute_benchmark_task(task)
        except Exception as e:
            return {"error": f"Full task failed: {str(e)}"}

    def _execute_custom_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行自定义脚本任务"""
        logger.info("Executing custom task - 自定义脚本")

        script_id = task.get("test_script_id")
        if not script_id:
            return {"error": "test_script_id is required for custom tasks"}

        try:
            # 从服务器获取脚本内容
            url = f"{self.server_url}/api/scripts/{script_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code != 200:
                return {"error": f"Failed to fetch script: {response.status_code}"}

            script_data = response.json()
            script_content = script_data.get("script_content") or script_data.get(
                "content"
            )

            if not script_content:
                return {"error": "Script content is empty"}

            # 写入临时脚本文件
            script_path = f"temp_script_{script_id}.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # 执行脚本
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=task.get("test_duration_seconds", 300) or 300,
            )

            # 清理临时文件
            try:
                os.remove(script_path)
            except:
                pass

            if result.returncode == 0:
                return {
                    "score": 100,
                    "output": result.stdout[:1000],
                    "status": "passed",
                }
            else:
                return {
                    "error": result.stderr[:500] or "Script execution failed",
                    "output": result.stdout[:500],
                }

        except subprocess.TimeoutExpired:
            return {"error": "Script execution timeout"}
        except Exception as e:
            return {"error": f"Custom task failed: {str(e)}"}

    def _calculate_cpu_score(self, hardware_info: Dict) -> float:
        """根据CPU信息计算分数"""
        try:
            cores = hardware_info.get("cpu_cores", 4)
            threads = hardware_info.get("cpu_threads", 8)
            base_clock = hardware_info.get("cpu_base_clock", 2.5)

            # 简单评分算法：核心数 * 主频 * 线程效率
            score = cores * base_clock * (threads / cores) * 10
            return min(score, 100)  # 上限100
        except:
            return 50

    def _calculate_gpu_score(self, hardware_info: Dict) -> float:
        """根据GPU信息计算分数"""
        try:
            vram = hardware_info.get("gpu_vram_mb", 0)
            gpu_model = hardware_info.get("gpu_model", "")

            # 简单评分算法：显存 * 100
            score = (vram / 1024) * 100  # 假设16GB=100分
            return min(score, 100)
        except:
            return 50

    def _calculate_memory_score(self, hardware_info: Dict) -> float:
        """根据内存信息计算分数"""
        try:
            total_gb = hardware_info.get("ram_total_gb", 8)

            # 简单评分算法：16GB=100分
            score = (total_gb / 16) * 100
            return min(score, 100)
        except:
            return 50

    def _calculate_disk_score(self, hardware_info: Dict) -> float:
        """根据磁盘信息计算分数"""
        try:
            disk_type = hardware_info.get("disk_type", "")

            # SSD=100, HDD=30
            if "ssd" in disk_type.lower() or "nvme" in disk_type.lower():
                return 100
            elif "hdd" in disk_type.lower() or "sata" in disk_type.lower():
                return 30
            return 50
        except:
            return 50

    def process_tasks(self):
        """处理待执行的任务"""
        while self.running:
            try:
                with self._task_lock:
                    if self.current_task_id:
                        # 已有任务在执行，跳过
                        time.sleep(1)
                        continue

                    task = self.poll_pending_tasks()
                    if task:
                        logger.info(f"Received task: {task.get('task_name')}")
                        self.execute_task(task)

            except Exception as e:
                logger.error(f"Error in task processor: {e}")

            time.sleep(5)  # 每5秒检查一次

    def start(self):
        """启动任务处理线程"""
        self.task_thread = threading.Thread(target=self.process_tasks, daemon=True)
        self.task_thread.start()
        logger.info("Task executor started")

    def stop(self):
        """停止任务处理"""
        self.running = False
        if self.task_thread:
            self.task_thread.join(timeout=5)
        logger.info("Task executor stopped")
