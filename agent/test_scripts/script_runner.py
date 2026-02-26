"""
测试脚本执行器
根据脚本定义执行各岗位测试场景，采集性能指标
"""

import os
import time
import json
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# 导入脚本定义
from test_scripts.script_definitions import (
    ALL_SCRIPTS, SCRIPT_CATEGORIES, PROGRAMMER_SCRIPTS,
    ARTIST_SCRIPTS, LEVEL_DESIGNER_SCRIPTS, TA_SCRIPTS,
    VFX_SCRIPTS, VIDEO_SCRIPTS
)

# 导入自动化框架
import sys
import os
# 确保 agent 目录在 Python 路径中
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from test_automation.automators import (
    TestContext, AutomatorFactory, run_automated_test
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptRunner:
    """测试脚本执行器"""
    
    def __init__(self, server_url: str = ""):
        self.server_url = server_url
        self.all_scripts = ALL_SCRIPTS
        self.categories = SCRIPT_CATEGORIES
        self.current_process: Optional[subprocess.Popen] = None
        self.metrics_history: List[Dict] = []
        self.collecting = False
    
    def get_script(self, script_id: str) -> Optional[Dict]:
        """获取脚本定义"""
        return self.all_scripts.get(script_id)
    
    def list_scripts(self, category: str = None) -> List[Dict]:
        """列出脚本"""
        if category:
            cat = self.categories.get(category)
            if cat:
                return [self.get_script(sid) for sid in cat["scripts"]]
        return list(self.all_scripts.values())
    
    def list_categories(self) -> List[Dict]:
        """列出岗位分类"""
        return [
            {"id": k, "name": v["name"], "script_count": len(v["scripts"])}
            for k, v in self.categories.items()
        ]
    
    def check_software_installed(self, software_name: str) -> Optional[str]:
        """检查软件是否安装，返回安装路径"""
        import wmi
        
        wmi_obj = wmi.WMI()
        
        # 方法1: 通过注册表查找
        try:
            import winreg
            uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            
            for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hkey, uninstall_key)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if software_name.lower() in name.lower():
                                    path = winreg.QueryValueEx(subkey, "InstallLocation")[0] if winreg.QueryValueEx(subkey, "InstallLocation")[0] else None
                                    if path:
                                        logger.info(f"Found {name} at {path}")
                                        return path
                            except:
                                pass
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            logger.warning(f"Registry scan failed: {e}")
        
        # 方法2: 通过进程检查是否运行
        try:
            for proc in __import__('psutil').process_iter(['name']):
                try:
                    if software_name.lower() in proc.info['name'].lower():
                        logger.info(f"Software is running: {proc.info['name']}")
                        return "running"
                except:
                    pass
        except:
            pass
        
        return None
    
    def find_software_path(self, script: Dict) -> Optional[str]:
        """查找软件安装路径"""
        software = script.get("software", "")
        
        # 常见软件安装路径
        common_paths = {
            "Unreal Engine": [
                r"C:\Program Files\Epic Games\UE_5.4",
                r"C:\Program Files\Epic Games\UE_5.3",
                r"C:\Program Files\Epic Games\UE_5.2",
                r"C:\Program Files\Epic Games\UE_5.1",
                r"C:\Program Files\Epic Games\UE_5.0",
                r"C:\Program Files\Epic Games\UE_4.27",
            ],
            "Visual Studio": [
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE",
                r"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE",
                r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE",
            ],
            "Maya": [
                r"C:\Program Files\Autodesk\Maya2024",
                r"C:\Program Files\Autodesk\Maya2023",
            ],
            "Blender": [
                r"C:\Program Files\Blender Foundation\Blender 4.0",
                r"C:\Program Files\Blender Foundation\Blender 3.6",
            ],
            "ZBrush": [
                r"C:\Program Files\Maxon ZBrush 2024",
                r"C:\Program Files\Maxon ZBrush 2023",
            ],
            "Substance Painter": [
                r"C:\Program Files\Adobe Adobe Substance 3D Painter 8.0",
                r"C:\Program Files\Adobe Adobe Substance 3D Painter 7.0",
            ],
            "Photoshop": [
                r"C:\Program Files\Adobe Adobe Photoshop 2024",
                r"C:\Program Files\Adobe Adobe Photoshop 2023",
            ],
            "Premiere Pro": [
                r"C:\Program Files\Adobe Adobe Premiere Pro 2024",
                r"C:\Program Files\Adobe Adobe Premiere Pro 2023",
            ],
            "After Effects": [
                r"C:\Program Files\Adobe After Effects 2024",
                r"C:\Program Files\Adobe After Effects 2023",
            ]
        }
        
        # 检查常见路径
        paths = common_paths.get(software, [])
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Found {software} at {path}")
                return path
        
        # 尝试注册表查找
        installed_path = self.check_software_installed(software)
        if installed_path and installed_path != "running":
            return installed_path
        
        return None
    
    def launch_software(self, script: Dict) -> bool:
        """启动测试软件"""
        software = script.get("software", "")
        scenario = script.get("scenario", "")
        
        # 查找软件路径
        software_path = self.find_software_path(script)
        
        if not software_path:
            logger.warning(f"Software not found: {software}")
            # 如果没找到，尝试直接启动
            software_path = software
        
        try:
            logger.info(f"Launching {software} for {scenario}...")
            self.current_process = subprocess.Popen(
                f'"{software_path}"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Process started with PID: {self.current_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch {software}: {e}")
            return False
    
    def wait_for_software(self, process_name: str, timeout: int = 30) -> bool:
        """等待软件启动"""
        import psutil
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            for proc in psutil.process_iter(['name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        logger.info(f"Process {process_name} is running")
                        return True
                except:
                    pass
            time.sleep(0.5)
        return False
    
    def stop_software(self, process_name: str):
        """停止软件"""
        import psutil
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    logger.info(f"Stopping {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except:
                        proc.kill()
            except:
                pass
    
    def collect_metrics(self, duration: int) -> List[Dict]:
        """采集性能指标"""
        import psutil
        
        history = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=0.5)
                
                # 内存
                mem = psutil.virtual_memory()
                
                # 磁盘
                disk_io = psutil.disk_io_counters()
                
                # 网络
                net_io = psutil.net_io_counters()
                
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": mem.percent,
                    "memory_used_mb": mem.used / (1024 * 1024),
                }
                
                if disk_io:
                    metrics["disk_read_mbps"] = disk_io.read_bytes / (1024 * 1024) / 0.5
                    metrics["disk_write_mbps"] = disk_io.write_bytes / (1024 * 1024) / 0.5
                
                if net_io:
                    metrics["network_sent_mb"] = net_io.bytes_sent / (1024 * 1024)
                    metrics["network_recv_mb"] = net_io.bytes_recv / (1024 * 1024)
                
                history.append(metrics)
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
        
        return history
    
    def execute_automated_script(
        self, 
        script_id: str,
        project_path: str = "",
        test_file: str = "",
        output_path: str = ""
    ) -> Dict:
        """使用自动化框架执行测试脚本
        
        Args:
            script_id: 脚本ID
            project_path: 项目文件路径（如 .sln, .uproject）
            test_file: 测试文件路径（如 .ma, .blend）
            output_path: 输出路径（用于导出/渲染）
        """
        script = self.get_script(script_id)
        
        if not script:
            return {
                "success": False,
                "error": f"Script not found: {script_id}"
            }
        
        result = {
            "script_id": script_id,
            "script_name": script.get("name"),
            "software": script.get("software"),
            "scenario": script.get("scenario"),
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "error": None,
            "metrics_summary": {},
            "automation_used": True
        }
        
        try:
            # 使用自动化框架执行测试
            logger.info(f"Running automated test: {script_id}")
            logger.info(f"  project_path: {project_path}")
            logger.info(f"  test_file: {test_file}")
            
            # 调用自动化测试
            auto_result = run_automated_test(
                script_id=script_id,
                software=script.get("software", ""),
                process_name=script.get("process_name", ""),
                scenario=script.get("scenario", ""),
                project_path=project_path,
                test_file=test_file
            )
            
            # 合并结果
            result["success"] = auto_result.get("success", False)
            result["error"] = auto_result.get("error")
            result["software_path"] = auto_result.get("software_path")
            result["metrics"] = auto_result.get("metrics", {})
            result["duration"] = auto_result.get("duration", 0)
            
            # 计算汇总
            metrics = result.get("metrics", {})
            if metrics:
                if "compile_time" in metrics:
                    result["metrics_summary"]["compile_time"] = metrics["compile_time"]
                if "render_time" in metrics:
                    result["metrics_summary"]["render_time"] = metrics["render_time"]
                if "test_time" in metrics:
                    result["metrics_summary"]["test_time"] = metrics["test_time"]
                if "build_time" in metrics:
                    result["metrics_summary"]["build_time"] = metrics["build_time"]
            
            logger.info(f"Automated test completed: {result['success']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Automated execution error: {e}")
        
        finally:
            result["end_time"] = datetime.utcnow().isoformat()
        
        return result
    
    def execute_script(self, script_id: str) -> Dict:
        """执行测试脚本"""
        script = self.get_script(script_id)
        
        if not script:
            return {
                "success": False,
                "error": f"Script not found: {script_id}"
            }
        
        result = {
            "script_id": script_id,
            "script_name": script.get("name"),
            "software": script.get("software"),
            "scenario": script.get("scenario"),
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": False,
            "error": None,
            "metrics_summary": {},
            "software_found": False,
            "software_path": None
        }
        
        try:
            # 1. 检查软件是否安装
            software_path = self.find_software_path(script)
            if software_path:
                result["software_found"] = True
                result["software_path"] = software_path
            else:
                result["error"] = f"Software not found: {script.get('software')}"
                logger.warning(result["error"])
                # 继续尝试启动
            
            # 2. 启动软件
            if result["software_found"] or not result["error"]:
                launched = self.launch_software(script)
                if launched:
                    # 等待软件启动
                    process_name = script.get("process_name", "")
                    if process_name:
                        self.wait_for_software(process_name, timeout=30)
            
            # 3. 采集指标
            duration = script.get("duration", 60)
            logger.info(f"Collecting metrics for {duration} seconds...")
            
            metrics = self.collect_metrics(duration)
            result["metrics"] = metrics
            
            # 4. 计算汇总
            if metrics:
                cpu_values = [m.get("cpu_percent", 0) for m in metrics]
                mem_values = [m.get("memory_percent", 0) for m in metrics]
                
                result["metrics_summary"] = {
                    "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    "max_cpu_percent": max(cpu_values) if cpu_values else 0,
                    "avg_memory_percent": sum(mem_values) / len(mem_values) if mem_values else 0,
                    "max_memory_percent": max(mem_values) if mem_values else 0,
                    "sample_count": len(metrics)
                }
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Script execution error: {e}")
        
        finally:
            # 5. 停止软件
            process_name = script.get("process_name", "")
            if process_name:
                self.stop_software(process_name)
            
            result["end_time"] = datetime.utcnow().isoformat()
        
        return result
    
    def get_available_tests(self, software_list: List[str]) -> List[Dict]:
        """获取可用的测试（根据已安装的软件）"""
        available = []
        
        for script_id, script in self.all_scripts.items():
            software = script.get("software", "")
            
            # 检查软件是否在列表中
            if software in software_list:
                available.append({
                    "script_id": script_id,
                    "name": script.get("name"),
                    "description": script.get("description"),
                    "software": software,
                    "category": self.get_category_for_script(script_id),
                    "duration": script.get("duration"),
                    "metrics": script.get("metrics")
                })
                continue
            
            # 检查软件是否已安装
            if self.find_software_path(script):
                available.append({
                    "script_id": script_id,
                    "name": script.get("name"),
                    "description": script.get("description"),
                    "software": software,
                    "category": self.get_category_for_script(script_id),
                    "duration": script.get("duration"),
                    "metrics": script.get("metrics"),
                    "installed": True
                })
        
        return available
    
    def get_category_for_script(self, script_id: str) -> str:
        """获取脚本所属分类"""
        for cat_id, cat in self.categories.items():
            if script_id in cat["scripts"]:
                return cat_id
        return "unknown"


def list_all_scripts():
    """列出所有测试脚本（供调试用）"""
    runner = ScriptRunner()
    
    print("\n" + "="*60)
    print("游戏公司各岗位测试脚本清单")
    print("="*60)
    
    for cat_id, cat in SCRIPT_CATEGORIES.items():
        print(f"\n【{cat['name']}】 ({len(cat['scripts'])}个)")
        print("-" * 40)
        
        for script_id in cat["scripts"]:
            script = PROGRAMMER_SCRIPTS.get(script_id) or \
                    ARTIST_SCRIPTS.get(script_id) or \
                    LEVEL_DESIGNER_SCRIPTS.get(script_id) or \
                    TA_SCRIPTS.get(script_id) or \
                    VFX_SCRIPTS.get(script_id) or \
                    VIDEO_SCRIPTS.get(script_id)
            
            if script:
                print(f"  {script_id}: {script['name']}")
                print(f"    软件: {script.get('software')}")
                print(f"    时长: {script.get('duration')}秒")
                print(f"    指标: {', '.join(script.get('metrics', []))}")
                print()


if __name__ == "__main__":
    list_all_scripts()
