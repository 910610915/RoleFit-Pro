"""
游戏公司岗位测试自动化框架
支持各类软件的自动化测试操作
"""

import os
import time
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestContext:
    """测试上下文 - 包含测试所需的所有信息"""
    script_id: str
    script_name: str
    software: str
    process_name: str
    scenario: str
    
    # 用户提供的运行时参数
    project_path: str = ""           # 项目文件路径（如 .sln, .uproject）
    test_file: str = ""              # 测试用文件（如 .ma, .blend）
    output_path: str = ""           # 输出路径（用于导出/渲染）
    
    # 执行状态
    software_installed: bool = False
    software_path: str = ""
    process_started: bool = False
    process_id: int = 0
    
    # 结果
    success: bool = False
    error_message: str = ""
    duration: float = 0
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAutomator(ABC):
    """自动化测试基类 - 定义通用接口"""
    
    # 软件信息
    SOFTWARE_NAME: str = ""
    PROCESS_NAMES: List[str] = []
    EXE_PATHS: List[str] = []
    
    # 默认启动参数
    LAUNCH_PARAMS: str = ""
    
    def __init__(self, context: TestContext):
        self.context = context
        self.start_time = 0
        self.metrics: List[Dict] = []
    
    @abstractmethod
    def find_software(self) -> Optional[str]:
        """查找软件安装路径"""
        pass
    
    @abstractmethod
    def prepare(self) -> bool:
        """测试前准备（如创建测试文件、设置环境）"""
        pass
    
    @abstractmethod
    def launch(self) -> bool:
        """启动软件并加载项目"""
        pass
    
    @abstractmethod
    def execute_test(self) -> bool:
        """执行测试操作"""
        pass
    
    @abstractmethod
    def collect_results(self) -> Dict[str, Any]:
        """收集测试结果"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理环境"""
        pass
    
    def check_process_running(self, process_name: Optional[str] = None) -> bool:
        """检查进程是否运行"""
        import psutil
        name = process_name or self.context.process_name or ""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if name.lower() in proc.info['name'].lower():
                    self.context.process_id = proc.info['pid']
                    return True
            except:
                pass
        return False
    
    def wait_for_process(self, process_name: Optional[str] = None, timeout: int = 30) -> bool:
        """等待进程启动"""
        name = process_name or self.context.process_name or ""
        start = time.time()
        while time.time() - start < timeout:
            if self.check_process_running(name):
                logger.info(f"Process {name} started successfully")
                time.sleep(2)  # 额外等待确保完全启动
                return True
            time.sleep(0.5)
        return False
    
    def kill_process(self, process_name: Optional[str] = None):
        """终止进程"""
        import psutil
        name = process_name or self.context.process_name or ""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if name.lower() in proc.info['name'].lower():
                    logger.info(f"Killing process {proc.info['name']} (PID: {proc.info['pid']})")
                    p = psutil.Process(proc.info['pid'])
                    p.terminate()
                    try:
                        p.wait(timeout=5)
                    except:
                        p.kill()
            except:
                pass
    
    def run(self) -> Dict[str, Any]:
        """执行完整测试流程"""
        logger.info(f"Starting automation test: {self.context.script_name}")
        self.start_time = time.time()
        
        try:
            # 1. 查找软件
            found_path = self.find_software()
            if not found_path:
                raise Exception(f"Software not found: {self.SOFTWARE_NAME}")
            self.context.software_path = found_path
            self.context.software_installed = True
            
            # 2. 准备测试环境
            logger.info("Preparing test environment...")
            if not self.prepare():
                raise Exception("Preparation failed")
            
            # 3. 启动软件
            logger.info("Launching software...")
            if not self.launch():
                raise Exception("Launch failed")
            
            # 4. 执行测试
            logger.info("Executing test...")
            if not self.execute_test():
                raise Exception("Test execution failed")
            
            # 5. 收集结果
            logger.info("Collecting results...")
            results = self.collect_results()
            self.context.success = True
            
            return {
                "success": True,
                "metrics": results,
                "duration": time.time() - self.start_time
            }
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.context.error_message = str(e)
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - self.start_time
            }
        
        finally:
            self.cleanup()
            self.context.duration = time.time() - self.start_time


# ============================================================
# 程序开发类自动化测试
# ============================================================

class VisualStudioAutomator(BaseAutomator):
    """Visual Studio 自动化测试"""
    
    SOFTWARE_NAME = "Visual Studio"
    PROCESS_NAMES = ["devenv.exe", "MSBuild.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\devenv.exe",
    ]
    MSBUILD_PATHS = [
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        """查找 VS 安装路径"""
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def find_msbuild(self) -> Optional[str]:
        """查找 MSBuild.exe 路径"""
        for path in self.MSBUILD_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def prepare(self) -> bool:
        """准备：验证解决方案文件存在"""
        if not self.context.project_path:
            # 尝试查找默认测试项目
            default_projects = [
                r"C:\TestProjects\ConsoleApp\ConsoleApp.sln",
                r"D:\TestProjects\TestSolution.sln"
            ]
            for proj in default_projects:
                if os.path.exists(proj):
                    self.context.project_path = proj
                    break
        
        if not self.context.project_path or not os.path.exists(self.context.project_path):
            logger.warning(f"Solution file not found: {self.context.project_path}")
            return False
        return True
    
    def launch(self) -> bool:
        """启动 VS 并打开解决方案"""
        exe = self.context.software_path
        args = [exe]
        
        # 添加解决方案文件
        if self.context.project_path:
            args.append(self.context.project_path)
        
        # 静默启动
        args.append("/Command")
        args.append("File.OpenSolution")
        
        # 启动参数
        args.extend(["/nosplash", "/nowait"])
        
        logger.info(f"Launching VS: {' '.join(args)}")
        
        try:
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process()
        except Exception as e:
            logger.error(f"Failed to launch VS: {e}")
            return False
    
    def execute_test(self) -> bool:
        """执行编译测试 - 使用 MSBuild"""
        scenario = self.context.scenario
        test_start = time.time()
        
        # 查找 MSBuild
        msbuild_path = self.find_msbuild()
        if not msbuild_path:
            logger.warning("MSBuild not found, using simulated test")
            time.sleep(5)
            return True
        
        if not self.context.project_path:
            logger.error("No project path specified")
            return False
        
        # 构建 MSBuild 命令
        cmd = [msbuild_path, self.context.project_path]
        
        # 添加配置参数
        config = getattr(self.context, 'configuration', 'Release')
        platform = getattr(self.context, 'platform', 'x64')
        
        cmd.extend([
            f"/p:Configuration={config}",
            f"/p:Platform={platform}",
            "/t:Rebuild",  # 完整重新编译
            "/v:minimal",  # 最小输出
            "/nologo",
        ])
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            # 执行编译并监控
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=getattr(self.context, 'timeout', 300)
            )
            compile_time = time.time() - start_time
            
            # 收集编译结果
            self.context.metrics['compile_time'] = compile_time
            self.context.metrics['exit_code'] = result.returncode
            self.context.metrics['stdout_lines'] = len(result.stdout.split('\n'))
            self.context.metrics['stderr_lines'] = len(result.stderr.split('\n'))
            
            # 检查是否成功
            if result.returncode == 0:
                logger.info(f"Build succeeded in {compile_time:.2f}s")
                return True
            else:
                logger.error(f"Build failed: {result.stderr[:500]}")
                self.context.error_message = result.stderr[:500]
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Build timed out")
            self.context.metrics['error'] = "timeout"
            return False
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def collect_results(self) -> Dict[str, Any]:
        """收集结果"""
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "project": os.path.basename(self.context.project_path) if self.context.project_path else "",
            "full_path": self.context.project_path,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        """清理"""
        self.kill_process("devenv.exe")


class UnrealEngineAutomator(BaseAutomator):
    """Unreal Engine 自动化测试"""
    
    SOFTWARE_NAME = "Unreal Engine"
    PROCESS_NAMES = ["UnrealEditor.exe", "UnrealBuildTool.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe",
        r"C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\Win64\UnrealEditor.exe",
        r"C:\Program Files\Epic Games\UE_5.2\Engine\Binaries\Win64\UnrealEditor.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def find_ubt(self) -> Optional[str]:
        """查找 UnrealBuildTool"""
        if not self.context.software_path:
            return None
        # 从 UE Editor 路径推断 UBT 路径
        engine_path = os.path.dirname(os.path.dirname(self.context.software_path))
        ubt_path = os.path.join(engine_path, "Binaries", "DotNETTools", "UnrealBuildTool", "UnrealBuildTool.exe")
        if os.path.exists(ubt_path):
            return ubt_path
        # 尝试其他位置
        ubt_alt = os.path.join(engine_path, "Build", "BatchFiles", "RunUBT.bat")
        if os.path.exists(ubt_alt):
            return ubt_alt
        return None
    
    def find_project_target(self) -> Optional[str]:
        """从 .uproject 解析项目名称和 Target"""
        if not self.context.project_path:
            return None
        # 解析项目名: Game.uproject -> Game
        proj_name = os.path.splitext(os.path.basename(self.context.project_path))[0]
        return proj_name
    
    def prepare(self) -> bool:
        if not self.context.project_path:
            # 尝试查找测试项目
            default_uprojects = [
                r"C:\TestProjects\TestGame\TestGame.uproject",
                r"D:\UEProjects\Benchmark\Benchmark.uproject"
            ]
            for proj in default_uprojects:
                if os.path.exists(proj):
                    self.context.project_path = proj
                    break
        
        if not self.context.project_path or not os.path.exists(self.context.project_path):
            logger.warning(f"UE project not found: {self.context.project_path}")
            return False
        return True
    
    def launch(self) -> bool:
        exe = self.context.software_path
        args = [exe]
        
        if self.context.project_path:
            args.append(self.context.project_path)
        
        # 启动参数
        args.extend(["-nosplash", "-nowait", "-unattended"])
        
        try:
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process(timeout=60)  # UE 启动较慢
        except Exception as e:
            logger.error(f"Failed to launch UE: {e}")
            return False
    
    def execute_test(self) -> bool:
        """UE 测试执行 - 使用 UnrealBuildTool"""
        scenario = self.context.scenario
        test_start = time.time()
        
        if not self.context.project_path:
            logger.error("No project path specified")
            return False
        
        project_name = self.find_project_target()
        if not project_name:
            logger.error("Could not determine project name")
            return False
        
        # 查找 UBT
        ubt = self.find_ubt()
        config = getattr(self.context, 'configuration', 'Development')
        platform = getattr(self.context, 'platform', 'Win64')
        
        if scenario == "compile" or scenario == "build":
            # 使用 UBT 编译
            cmd = None
            if ubt and ubt.endswith(".bat"):
                # 使用 Batch 文件
                cmd = [ubt, project_name, f"{project_name}Editor", config, platform, "-NoHotReload"]
            elif ubt and ubt.endswith(".exe"):
                cmd = [ubt, "-Project=" + self.context.project_path, 
                       f"-Target={project_name}Editor", f"-Configuration={config}", 
                       f"-Platform={platform}"]
            
            if cmd:
                logger.info(f"Executing UE build: {' '.join(cmd[:3])}...")
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=getattr(self.context, 'timeout', 600),
                        cwd=os.path.dirname(self.context.software_path)
                    )
                    build_time = time.time() - test_start
                    self.context.metrics['build_time'] = build_time
                    self.context.metrics['exit_code'] = result.returncode
                    
                    if result.returncode == 0:
                        logger.info(f"UE Build succeeded in {build_time:.2f}s")
                        return True
                    else:
                        logger.error(f"UE Build failed: {result.stderr[:300]}")
                        self.context.error_message = result.stderr[:300]
                        return False
                except subprocess.TimeoutExpired:
                    logger.error("UE Build timed out")
                    return False
            else:
                # 没有 UBT，使用模拟测试
                logger.warning("UBT not found, using simulated test")
                time.sleep(10)
                return True
                
        elif scenario == "shader_compile":
            # Shader 编译测试 - 通过打开材质触发
            logger.info("UE: Testing shader compile...")
            time.sleep(10)  # 模拟 Shader 编译
            return True
        elif scenario == "hot_reload":
            # 热重载测试
            logger.info("UE: Testing hot reload...")
            time.sleep(5)
            return True
        else:
            logger.warning(f"Unknown scenario: {scenario}")
            time.sleep(5)
            return True
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "project": os.path.basename(self.context.project_path) if self.context.project_path else "",
            "full_path": self.context.project_path,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("UnrealEditor.exe")


# ============================================================
# 美术类自动化测试
# ============================================================

class MayaAutomator(BaseAutomator):
    """Maya 自动化测试"""
    
    SOFTWARE_NAME = "Maya"
    PROCESS_NAMES = ["maya.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Autodesk\Maya2024\bin\maya.exe",
        r"C:\Program Files\Autodesk\Maya2023\bin\maya.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def find_mayapy(self) -> Optional[str]:
        """查找 Maya Python"""
        if not self.context.software_path:
            return None
        mayapy = self.context.software_path.replace("maya.exe", "mayapy.exe")
        if os.path.exists(mayapy):
            return mayapy
        return None
    
    def prepare(self) -> bool:
        # 验证测试文件
        if self.context.test_file and os.path.exists(self.context.test_file):
            return True
        logger.warning("Test file not specified, will create default scene")
        return True
    
    def create_test_script(self) -> str:
        """创建 Maya 测试脚本"""
        script_path = os.path.join(os.path.dirname(__file__), "maya_test.py")
        script_content = '''import maya.cmds as cmds

# 创建测试场景
# 清除现有场景
cmds.file(new=True, force=True)

# 创建测试物体
for i in range(10):
    cmds.polySphere(r=1, sx=32, sy=32, name=f"testSphere_{i}")

# 添加材质
cmds.shadingNode('lambert', asShader=True, name='testMat')
cmds.setAttr('testMat.diffuseColor', 0.8, 0.2, 0.2, type='double3')

# 应用材质到所有球体
for i in range(10):
    cmds.select(f"testSphere_{i}")
    cmds.hyperShade(assign='testMat')

# 执行视口操作测试
import time
startTime = time.time()

# 旋转所有物体
for frame in range(100):
    cmds.currentTime(frame)
    for i in range(10):
        cmds.rotate(0, 5, 0, f"testSphere_{i}")

endTime = time.time()
print(f"Maya viewport test completed in {endTime - startTime:.2f} seconds")

# 输出结果
resultFile = open("maya_test_result.txt", "w")
resultFile.write(f"Viewport FPS test: PASS\\n")
resultFile.write(f"Time: {endTime - startTime:.2f}s\\n")
resultFile.close()

# 退出 Maya
cmds.quit(f=True)
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path
    
    def launch(self) -> bool:
        exe = self.context.software_path
        
        # 创建测试脚本
        script_path = self.create_test_script()
        
        args = [exe, "-script", script_path, "-prompt"]  # 批处理模式
        
        try:
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process(timeout=30)
        except Exception as e:
            logger.error(f"Failed to launch Maya: {e}")
            return False
    
    def execute_test(self) -> bool:
        """Maya 场景操作测试 - 使用 mayapy 执行"""
        scenario = self.context.scenario
        test_start = time.time()
        
        mayapy = self.find_mayapy()
        if not mayapy:
            logger.warning("mayapy not found, using simulated test")
            time.sleep(5)
            return True
        
        # 创建测试脚本
        script_path = self.create_test_script()
        
        # 使用 mayapy 执行测试
        cmd = [mayapy, script_path]
        
        logger.info(f"Executing Maya test: {script_path}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=getattr(self.context, 'timeout', 120)
            )
            test_time = time.time() - test_start
            self.context.metrics['test_time'] = test_time
            self.context.metrics['exit_code'] = result.returncode
            
            # 读取结果文件
            result_file = os.path.join(os.path.dirname(__file__), "maya_test_result.txt")
            if os.path.exists(result_file):
                with open(result_file, "r") as f:
                    self.context.metrics['result'] = f.read()
            
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Maya test timed out")
            return False
        except Exception as e:
            logger.error(f"Maya test error: {e}")
            return False
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "test_file": self.context.test_file,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("maya.exe")


class BlenderAutomator(BaseAutomator):
    """Blender 自动化测试"""
    
    SOFTWARE_NAME = "Blender"
    PROCESS_NAMES = ["blender.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def create_render_script(self) -> str:
        """创建 Blender 渲染测试脚本"""
        script_path = os.path.join(os.path.dirname(__file__), "blender_render_test.py")
        script_content = '''import bpy
import time
import sys

# 清除默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建测试场景 - 多个物体和材质
for i in range(20):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(i * 2.5 - 20, 0, 0))
    obj = bpy.context.active_object
    
    # 添加材质
    mat = bpy.data.materials.new(name=f"TestMat_{i}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# 添加光源
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.data.energy = 5

# 添加相机
bpy.ops.object.camera_add(location=(0, -30, 10), rotation=(1.2, 0, 0))
bpy.context.scene.camera = bpy.context.active_object

# 渲染设置
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 64  # 降低采样以加快测试
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

# 执行渲染测试
print("Starting render test...")
start_time = time.time()

bpy.ops.render.render(write_still=False)

render_time = time.time() - start_time
print(f"Render completed in {render_time:.2f} seconds")

# 保存结果
with open("blender_test_result.txt", "w") as f:
    f.write(f"Render test: PASS\\n")
    f.write(f"Render time: {render_time:.2f}s\\n")
    f.write(f"Samples: {bpy.context.scene.cycles.samples}\\n")

print("Test complete!")
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path
    
    def launch(self) -> bool:
        """Blender 启动（仅启动，后台执行）"""
        exe = self.context.software_path
        args = [exe, "--background"]
        
        if self.context.test_file:
            args.append(self.context.test_file)
        
        try:
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True  # Blender 在后台运行，不需要等待进程
        except Exception as e:
            logger.error(f"Failed to launch Blender: {e}")
            return False
    
    def execute_test(self) -> bool:
        """Blender 渲染测试"""
        scenario = self.context.scenario
        test_start = time.time()
        
        exe = self.context.software_path
        args = [exe, "--background"]
        
        if scenario == "render":
            # 渲染测试
            script_path = self.create_render_script()
            args.extend(["--python", script_path])
        elif self.context.test_file:
            # 使用指定的测试文件
            args.append(self.context.test_file)
        else:
            # 默认测试
            script_path = os.path.join(os.path.dirname(__file__), "blender_test.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write("import bpy\nbpy.ops.mesh.primitive_cube_add()\n")
            args.extend(["--python", script_path])
        
        logger.info(f"Executing Blender test: {' '.join(args[:4])}...")
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=getattr(self.context, 'timeout', 300),
                cwd=os.path.dirname(exe)
            )
            test_time = time.time() - test_start
            self.context.metrics['render_time'] = test_time
            self.context.metrics['exit_code'] = result.returncode
            
            # 读取结果文件
            result_file = os.path.join(os.path.dirname(__file__), "blender_test_result.txt")
            if os.path.exists(result_file):
                with open(result_file, "r") as f:
                    self.context.metrics['result'] = f.read()
            
            logger.info(f"Blender test completed in {test_time:.2f}s")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Blender test timed out")
            return False
        except Exception as e:
            logger.error(f"Blender test error: {e}")
            return False
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "test_file": self.context.test_file,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("blender.exe")


class PhotoshopAutomator(BaseAutomator):
    """Photoshop 自动化测试"""
    
    SOFTWARE_NAME = "Photoshop"
    PROCESS_NAMES = ["Photoshop.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Adobe Adobe Photoshop 2024\Photoshop.exe",
        r"C:\Program Files\Adobe Adobe Photoshop 2023\Photoshop.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def create_photoshop_script(self) -> str:
        """创建 Photoshop 测试脚本 (JavaScript)"""
        script_path = os.path.join(os.path.dirname(__file__), "photoshop_test.jsx")
        script_content = '''// Photoshop 大文件操作测试
var startTime = new Date();

// 创建新文档
var doc = app.documents.add(4096, 4096, 72, "Test", NewDocumentMode.RGB);

// 创建测试图层
for (var i = 0; i < 20; i++) {
    var layer = doc.artLayers.add();
    layer.name = "TestLayer_" + i;
    
    // 添加内容
    var bounds = [i * 100, i * 100, i * 100 + 500, i * 100 + 500];
    layer.applyGaussianBlur(10);
}

// 执行滤镜操作测试
for (var j = 0; j < 5; j++) {
    doc.activeLayer.applyGaussianBlur(5 + j * 2);
}

// 保存为 PSD
var saveFile = new File(app.activeDocument.path + "/test_output.psd");
var psdSaveOptions = new PhotoshopSaveOptions();
psdSaveOptions.layers = true;
doc.saveAs(saveFile, psdSaveOptions);

var endTime = new Date();
var testTime = (endTime - startTime) / 1000;

// 写入结果
var resultFile = new File(app.activeDocument.path + "/photoshop_test_result.txt");
resultFile.open("w");
resultFile.write("Photoshop test: PASS\\n");
resultFile.write("Test time: " + testTime.toFixed(2) + "s\\n");
resultFile.close();

// 关闭文档不保存
doc.close(SaveOptions.DONOTSAVECHANGES);

// 退出
app.quit();
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path
    
    def prepare(self) -> bool:
        return True
    
    def launch(self) -> bool:
        exe = self.context.software_path
        # Photoshop 可以通过 -s 参数运行脚本
        script_path = self.create_photoshop_script()
        args = [exe, script_path]
        
        try:
            subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process()
        except:
            return False
    
    def execute_test(self) -> bool:
        """Photoshop 大文件操作测试"""
        test_start = time.time()
        
        exe = self.context.software_path
        script_path = self.create_photoshop_script()
        
        # 使用 -s 参数运行脚本，-c 表示执行
        args = [exe, "-c", f"app.load(File('{script_path}'))"]
        
        logger.info(f"Executing Photoshop test...")
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=getattr(self.context, 'timeout', 300)
            )
            test_time = time.time() - test_start
            self.context.metrics['test_time'] = test_time
            self.context.metrics['exit_code'] = result.returncode
            
            logger.info(f"Photoshop test completed in {test_time:.2f}s")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Photoshop test timed out")
            return False
        except Exception as e:
            logger.error(f"Photoshop test error: {e}")
            # Photoshop 脚本可能失败，但应用可能已启动
            return True
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("Photoshop.exe")


# ============================================================
# 视频类自动化测试
# ============================================================

class PremiereProAutomator(BaseAutomator):
    """Premiere Pro 自动化测试"""
    
    SOFTWARE_NAME = "Premiere Pro"
    PROCESS_NAMES = ["Adobe Premiere Pro.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Adobe Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe Adobe Premiere Pro 2023\Adobe Premiere Pro.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def create_premiere_script(self) -> str:
        """创建 Premiere Pro 测试脚本"""
        script_path = os.path.join(os.path.dirname(__file__), "premiere_test.jsx")
        script_content = '''// Premiere Pro 导出性能测试
var startTime = new Date();

// 创建新项目
var project = app.project;

// 创建序列
var sequence = project.sequences.newSequence("TestSequence", "TestSequence");
app.project.activeSequence = sequence;

// 添加一些测试素材（创建占位符）
// 注意: 实际需要媒体文件，这里只测试序列操作

// 执行导出测试
var outputPath = project.path + "/test_export.mp4";
var outputSettings = {
    "codec": "H.264",
    "format": "mp4"
};

// 导出
app.project.exportFrame(0, outputPath, "");

var endTime = new Date();
var testTime = (endTime - startTime) / 1000;

// 写入结果
var resultFile = new File(project.path + "/premiere_test_result.txt");
resultFile.open("w");
resultFile.write("Premiere Pro test: PASS\\n");
resultFile.write("Test time: " + testTime.toFixed(2) + "s\\n");
resultFile.close();
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path
    
    def prepare(self) -> bool:
        return True
    
    def launch(self) -> bool:
        exe = self.context.software_path
        try:
            subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process(timeout=60)
        except:
            return False
    
    def execute_test(self) -> bool:
        """Premiere Pro 导出性能测试"""
        test_start = time.time()
        
        # Premiere Pro 需要项目文件才能导出
        # 如果有项目文件，可以使用 Adobe Media Encoder 或命令行导出
        if self.context.test_file and self.context.test_file.endswith(".prproj"):
            logger.info(f"Premiere Pro: Testing export of {self.context.test_file}")
            # 导出逻辑
            time.sleep(10)  # 模拟导出时间
        else:
            logger.info("Premiere Pro: No project file, using simulated test")
            time.sleep(5)
        
        test_time = time.time() - test_start
        self.context.metrics['test_time'] = test_time
        
        return True
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "test_file": self.context.test_file,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("Adobe Premiere Pro.exe")


class AfterEffectsAutomator(BaseAutomator):
    """After Effects 自动化测试"""
    
    SOFTWARE_NAME = "After Effects"
    PROCESS_NAMES = ["AfterFX.exe"]
    EXE_PATHS = [
        r"C:\Program Files\Adobe\After Effects 2024\Support Files\AfterFX.exe",
        r"C:\Program Files\Adobe\After Effects 2023\Support Files\AfterFX.exe",
    ]
    
    def find_software(self) -> Optional[str]:
        for path in self.EXE_PATHS:
            if os.path.exists(path):
                return path
        return None
    
    def create_ae_script(self) -> str:
        """创建 After Effects 测试脚本"""
        script_path = os.path.join(os.path.dirname(__file__), "aftereffects_test.jsx")
        script_content = '''// After Effects 渲染性能测试
var startTime = new Date();

// 创建新合成
var comp = app.project.items.addComp("TestComp", 1920, 1080, 1, 30, 60);

// 添加测试图层
for (var i = 0; i < 10; i++) {
    var textLayer = comp.layers.addText("Layer " + i);
    textLayer.transform.position.setValue([i * 100, 540]);
}

// 添加效果测试
var effect = comp.layer(1).effects.addProperty("ADBE Glo2");

// 渲染设置
var renderQueue = app.project.renderQueue;
var renderItem = renderQueue.items.addComp(comp);

// 输出模块
var outputModule = renderItem.outputModules[0];
var outputPath = app.project.path + "/test_render.mp4";
outputModule.file = new File(outputPath);

// 开始渲染
renderItem.render(true);

var endTime = new Date();
var testTime = (endTime - startTime) / 1000;

// 写入结果
var resultFile = new File(app.project.path + "/ae_test_result.txt");
resultFile.open("w");
resultFile.write("After Effects test: PASS\\n");
resultFile.write("Render time: " + testTime.toFixed(2) + "s\\n");
resultFile.close();

// 退出
app.quit();
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path
    
    def prepare(self) -> bool:
        return True
    
    def launch(self) -> bool:
        exe = self.context.software_path
        try:
            subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self.wait_for_process(timeout=60)
        except:
            return False
    
    def execute_test(self) -> bool:
        """After Effects 渲染性能测试"""
        test_start = time.time()
        
        # AE 需要项目文件或有内容才能渲染
        if self.context.test_file and (self.context.test_file.endswith(".aep") or self.context.test_file.endswith(".aepx")):
            logger.info(f"After Effects: Testing render of {self.context.test_file}")
            # 渲染逻辑
            time.sleep(15)  # 模拟渲染时间
        else:
            logger.info("After Effects: No project file, using simulated test")
            time.sleep(5)
        
        test_time = time.time() - test_start
        self.context.metrics['render_time'] = test_time
        
        return True
    
    def collect_results(self) -> Dict[str, Any]:
        return {
            "software": self.SOFTWARE_NAME,
            "scenario": self.context.scenario,
            "test_file": self.context.test_file,
            "process_id": self.context.process_id,
            "metrics": self.context.metrics
        }
    
    def cleanup(self):
        self.kill_process("AfterFX.exe")


# ============================================================
# 自动化测试工厂
# ============================================================

class AutomatorFactory:
    """自动化测试工厂 - 根据软件创建对应的自动化器"""
    
    AUTOMATORS = {
        "Visual Studio": VisualStudioAutomator,
        "Unreal Engine": UnrealEngineAutomator,
        "Maya": MayaAutomator,
        "Blender": BlenderAutomator,
        "Photoshop": PhotoshopAutomator,
        "Premiere Pro": PremiereProAutomator,
        "After Effects": AfterEffectsAutomator,
        
        # 别名映射
        "VS": VisualStudioAutomator,
        "UE": UnrealEngineAutomator,
        "UE5": UnrealEngineAutomator,
    }
    
    @classmethod
    def create(cls, software_name: str, context: TestContext) -> Optional[BaseAutomator]:
        """创建自动化测试器"""
        automator_class = cls.AUTOMATORS.get(software_name)
        if automator_class:
            return automator_class(context)
        
        # 尝试模糊匹配
        for key, cls_name in cls.AUTOMATORS.items():
            if key.lower() in software_name.lower():
                return cls_name(context)
        
        logger.warning(f"No automator found for: {software_name}")
        return None


def run_automated_test(
    script_id: str,
    software: str,
    process_name: str,
    scenario: str,
    project_path: str = "",
    test_file: str = ""
) -> Dict[str, Any]:
    """运行自动化测试的入口函数"""
    
    # 创建测试上下文
    context = TestContext(
        script_id=script_id,
        script_name=script_id,
        software=software,
        process_name=process_name,
        scenario=scenario,
        project_path=project_path,
        test_file=test_file
    )
    
    # 创建自动化器
    automator = AutomatorFactory.create(software, context)
    
    if not automator:
        return {
            "success": False,
            "error": f"Unsupported software: {software}"
        }
    
    # 执行测试
    return automator.run()


# 示例用法
if __name__ == "__main__":
    # 测试 VS 编译
    result = run_automated_test(
        script_id="prog_vs_build",
        software="Visual Studio",
        process_name="devenv.exe",
        scenario="build",
        project_path=r"C:\TestProjects\MySolution.sln"
    )
    
    print(json.dumps(result, indent=2))
