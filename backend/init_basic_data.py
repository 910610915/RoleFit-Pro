"""
初始化基础数据脚本
用于在新环境中初始化脚本和软件数据
"""

import uuid
from datetime import datetime

from sqlalchemy import select, func
from app.core.database import SyncSessionLocal
from app.models.sqlite import JobScript, TestSoftware


def init_basic_data():
    """
    初始化基础数据（软件和脚本）
    在新环境中运行此函数来创建基础数据
    """
    session = SyncSessionLocal()

    try:
        # 检查是否已有数据
        sw_count = session.execute(select(func.count(TestSoftware.id))).scalar()
        script_count = session.execute(select(func.count(JobScript.id))).scalar()

        if sw_count > 0 and script_count > 0:
            print(f"基础数据已存在: {sw_count} 个软件, {script_count} 个脚本")
            return

        print("开始初始化基础数据...")

        # ==================== 添加软件 ====================
        software_list = [
            {"name": "Unreal Engine 5", "code": "UE5", "category": "DEV"},
            {"name": "Unreal Engine 4", "code": "UE4", "category": "DEV"},
            {"name": "Unity 2023", "code": "UNITY2023", "category": "DEV"},
            {"name": "Visual Studio 2022", "code": "VS2022", "category": "DEV"},
            {
                "name": "Visual Studio",
                "code": "VS",
                "category": "DEV",
                "icon": "/software-logos/Visual Studio.png",
                "desc": "Visual Studio 标准测试支持",
            },
            {
                "name": "Unreal Engine",
                "code": "UE",
                "category": "DEV",
                "icon": "/software-logos/Unreal Engine.png",
                "desc": "Unreal Engine 标准测试支持",
            },
            {"name": "Photoshop 2024", "code": "PS2024", "category": "ART"},
            {
                "name": "Photoshop",
                "code": "PS",
                "category": "ART",
                "icon": "/software-logos/Photoshop.png",
                "desc": "Photoshop 标准测试支持",
            },
            {"name": "Maya 2024", "code": "MAYA", "category": "ART"},
            {
                "name": "Blender",
                "code": "BLENDER",
                "category": "ART",
                "icon": "/software-logos/Blender.png",
                "desc": "Blender 标准测试支持",
            },
            {
                "name": "ZBrush",
                "code": "ZBRUSH",
                "category": "ART",
                "icon": "/software-logos/3Dmax.png",
                "desc": "ZBrush 标准测试支持",
            },
            {
                "name": "Substance Painter",
                "code": "SP",
                "category": "ART",
                "icon": "/software-logos/Photoshop.png",
                "desc": "Substance Painter 标准测试支持",
            },
            {
                "name": "Premiere Pro",
                "code": "PR",
                "category": "VIDEO",
                "icon": "/software-logos/Premiere Pro.png",
                "desc": "Premiere Pro 标准测试支持",
            },
            {"name": "After Effects 2024", "code": "AE2024", "category": "VFX"},
            {
                "name": "After Effects",
                "code": "AE",
                "category": "VFX",
                "icon": "/software-logos/After Effects.png",
                "desc": "After Effects 标准测试支持",
            },
            {"name": "Figma", "code": "FIGMA", "category": "UI"},
        ]

        software_map = {}
        for sw in software_list:
            sw_obj = TestSoftware(
                id=str(uuid.uuid4()),
                software_name=sw["name"],
                software_code=sw["code"],
                category=sw["category"],
                icon=sw.get("icon"),
                description=sw.get("desc"),
                software_type="portable",
                detection_method="process" if sw.get("icon") else "file",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(sw_obj)
            software_map[sw["code"]] = sw_obj.id

        session.commit()
        print(f"添加了 {len(software_list)} 个软件")

        # ==================== 添加脚本 ====================
        script_list = [
            # UE 脚本
            {
                "name": "UE5启动测试",
                "code": "UE5_START_TEST",
                "software": "UE5",
                "type": "START",
                "duration": 60,
            },
            {
                "name": "UE项目编译测试",
                "code": "prog_ue_compile",
                "software": "UE",
                "type": "BENCHMARK",
                "duration": 300,
            },
            {
                "name": "Shader编译测试",
                "code": "prog_shader_compile",
                "software": "UE",
                "type": "BENCHMARK",
                "duration": 120,
            },
            {
                "name": "WorldPartition大地图测试",
                "code": "ld_ue_worldpartition",
                "software": "UE",
                "type": "WORLD_PARTITION",
                "duration": 180,
            },
            {
                "name": "蓝图编译测试",
                "code": "prog_blueprint_compile",
                "software": "UE",
                "type": "BENCHMARK",
                "duration": 120,
            },
            {
                "name": "关卡加载测试",
                "code": "ld_ue_level_load",
                "software": "UE",
                "type": "LOAD",
                "duration": 120,
            },
            {
                "name": "VFX场景编辑测试",
                "code": "vfx_scene",
                "software": "UE",
                "type": "VFX_SCENE_EDIT",
                "duration": 120,
            },
            {
                "name": "角色动画编辑",
                "code": "art_character_animation",
                "software": "UE",
                "type": "ANIMATION",
                "duration": 120,
            },
            {
                "name": "光照构建测试",
                "code": "art_lighting_build",
                "software": "UE",
                "type": "LIGHTING",
                "duration": 180,
            },
            {
                "name": "材质编辑器测试",
                "code": "art_material_editor",
                "software": "UE",
                "type": "MATERIAL",
                "duration": 60,
            },
            # Unity 脚本
            {
                "name": "Unity启动测试",
                "code": "UNITY_START_TEST",
                "software": "UNITY2023",
                "type": "START",
                "duration": 60,
            },
            {
                "name": "Unity项目编译",
                "code": "prog_unity_compile",
                "software": "UNITY2023",
                "type": "BENCHMARK",
                "duration": 180,
            },
            # VS 脚本
            {
                "name": "Visual Studio启动测试",
                "code": "VS_START_TEST",
                "software": "VS",
                "type": "START",
                "duration": 60,
            },
            {
                "name": "VS解决方案编译",
                "code": "prog_vs_compile",
                "software": "VS",
                "type": "BENCHMARK",
                "duration": 300,
            },
            {
                "name": "VS项目调试",
                "code": "prog_vs_debug",
                "software": "VS",
                "type": "DEBUG",
                "duration": 120,
            },
            # Photoshop 脚本
            {
                "name": "Photoshop启动测试",
                "code": "PS_START_TEST",
                "software": "PS",
                "type": "START",
                "duration": 30,
            },
            {
                "name": "PSD文件打开测试",
                "code": "art_psd_open",
                "software": "PS",
                "type": "FILE_OPERATION",
                "duration": 60,
            },
            {
                "name": "滤镜效果测试",
                "code": "art_filter_apply",
                "software": "PS",
                "type": "FILTER",
                "duration": 60,
            },
            {
                "name": "3D渲染测试",
                "code": "art_3d_render",
                "software": "PS",
                "type": "RENDER",
                "duration": 120,
            },
            # Maya 脚本
            {
                "name": "Maya启动测试",
                "code": "MAYA_START_TEST",
                "software": "MAYA",
                "type": "START",
                "duration": 60,
            },
            {
                "name": "Maya场景打开",
                "code": "art_maya_open",
                "software": "MAYA",
                "type": "FILE_OPERATION",
                "duration": 60,
            },
            {
                "name": "Maya动画播放",
                "code": "art_maya_playback",
                "software": "MAYA",
                "type": "PLAYBACK",
                "duration": 60,
            },
            {
                "name": "Maya渲染测试",
                "code": "art_maya_render",
                "software": "MAYA",
                "type": "RENDER",
                "duration": 300,
            },
            # Blender 脚本
            {
                "name": "Blender启动测试",
                "code": "BLENDER_START_TEST",
                "software": "BLENDER",
                "type": "START",
                "duration": 30,
            },
            {
                "name": "Blender场景测试",
                "code": "art_blender_scene",
                "software": "BLENDER",
                "type": "SCENE",
                "duration": 60,
            },
            {
                "name": "Blender渲染测试",
                "code": "art_blender_render",
                "software": "BLENDER",
                "type": "RENDER",
                "duration": 300,
            },
            # 其他
            {
                "name": "空闲测试",
                "code": "IDLE_TEST",
                "software": None,
                "type": "OPERATION",
                "duration": 30,
            },
            {
                "name": "压力测试",
                "code": "STRESS_TEST",
                "software": None,
                "type": "STRESS",
                "duration": 300,
            },
        ]

        for script in script_list:
            sw_id = software_map.get(script["software"])

            # 构建脚本内容
            content = {
                "name": script["name"],
                "description": f"{script['name']} 测试脚本",
                "software": script["software"],
                "scenario": script["type"].lower(),
                "duration": script["duration"],
                "steps": ["执行测试操作", "记录性能指标", "生成测试报告"],
            }

            import json

            script_obj = JobScript(
                id=str(uuid.uuid4()),
                script_name=script["name"],
                script_code=script["code"],
                software_id=sw_id,
                script_type=script["type"],
                script_content=json.dumps(content, ensure_ascii=False),
                expected_duration=script["duration"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(script_obj)

        session.commit()
        print(f"添加了 {len(script_list)} 个脚本")
        print("基础数据初始化完成！")

    except Exception as e:
        print(f"初始化数据时出错: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    init_basic_data()
