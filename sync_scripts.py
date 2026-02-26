"""
同步测试脚本到数据库
"""

import sqlite3
import json

# 测试脚本定义
SCRIPTS = [
    # 程序开发
    {
        "script_code": "prog_ue_compile",
        "script_name": "UE项目编译测试",
        "description": "测试UE5项目完整编译性能，包括C++和蓝图",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "compile",
        "duration": 300,
        "metrics": ["cpu_percent", "memory_mb", "disk_write_mbps", "compile_time"],
        "category": "programmer"
    },
    {
        "script_code": "prog_vs_build",
        "script_name": "Visual Studio编译测试",
        "description": "测试VS2022解决方案编译性能",
        "software": "Visual Studio",
        "process_name": "devenv.exe",
        "scenario": "build",
        "duration": 180,
        "metrics": ["cpu_percent", "memory_mb", "compile_time"],
        "category": "programmer"
    },
    {
        "script_code": "prog_shader_compile",
        "script_name": "Shader编译测试",
        "description": "测试UE材质/Shader首次编译性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "shader_compile",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "gpu_memory_mb", "compile_time"],
        "category": "programmer"
    },
    {
        "script_code": "prog_hot_reload",
        "script_name": "HotReload测试",
        "description": "测试代码热重载性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "hot_reload",
        "duration": 60,
        "metrics": ["cpu_percent", "memory_mb", "reload_time"],
        "category": "programmer"
    },
    {
        "script_code": "prog_debug",
        "script_name": "调试模式测试",
        "description": "测试VS调试模式性能",
        "software": "Visual Studio",
        "process_name": "devenv.exe",
        "scenario": "debug",
        "duration": 90,
        "metrics": ["cpu_percent", "memory_mb"],
        "category": "programmer"
    },
    # 美术
    {
        "script_code": "art_maya_scene",
        "script_name": "Maya场景编辑测试",
        "description": "测试Maya复杂场景viewport操作性能",
        "software": "Maya",
        "process_name": "maya.exe",
        "scenario": "scene_edit",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "viewport_fps"],
        "category": "artist"
    },
    {
        "script_code": "art_blender_model",
        "script_name": "Blender建模测试",
        "description": "测试Blender多边形建模性能",
        "software": "Blender",
        "process_name": "blender.exe",
        "scenario": "modeling",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "viewport_fps"],
        "category": "artist"
    },
    {
        "script_code": "art_zbrush_sculpt",
        "script_name": "ZBrush雕刻测试",
        "description": "测试ZBrush高精度模型雕刻性能",
        "software": "ZBrush",
        "process_name": "ZBrush.exe",
        "scenario": "sculpt",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb"],
        "category": "artist"
    },
    {
        "script_code": "art_substance_paint",
        "script_name": "Substance纹理制作测试",
        "description": "测试Substance Painter纹理处理性能",
        "software": "Substance Painter",
        "process_name": "Adobe Substance 3D Painter.exe",
        "scenario": "texture_paint",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "gpu_memory_mb"],
        "category": "artist"
    },
    {
        "script_code": "art_ps_large",
        "script_name": "Photoshop大图测试",
        "description": "测试Photoshop处理大尺寸图像性能",
        "software": "Photoshop",
        "process_name": "Photoshop.exe",
        "scenario": "large_image",
        "duration": 90,
        "metrics": ["cpu_percent", "memory_mb", "gpu_memory_mb", "operation_time"],
        "category": "artist"
    },
    {
        "script_code": "art_maya_playback",
        "script_name": "Maya动画播放测试",
        "description": "测试Maya复杂动画播放流畅度",
        "software": "Maya",
        "process_name": "maya.exe",
        "scenario": "animation_playback",
        "duration": 60,
        "metrics": ["gpu_percent", "memory_mb", "playback_fps"],
        "category": "artist"
    },
    # 地编
    {
        "script_code": "ld_ue_level",
        "script_name": "UE关卡编辑测试",
        "description": "测试UE5大场景关卡编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "level_edit",
        "duration": 180,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "gpu_memory_mb", "editor_fps"],
        "category": "level_designer"
    },
    {
        "script_code": "ld_ue_lighting",
        "script_name": "UE光照烘焙测试",
        "description": "测试UE5光照构建性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "light_build",
        "duration": 600,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "build_time"],
        "category": "level_designer"
    },
    {
        "script_code": "ld_ue_navmesh",
        "script_name": "NavMesh构建测试",
        "description": "测试导航网格生成性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "navmesh_build",
        "duration": 300,
        "metrics": ["cpu_percent", "memory_mb", "build_time"],
        "category": "level_designer"
    },
    {
        "script_code": "ld_ue_streaming",
        "script_name": "UE纹理流送测试",
        "description": "测试大地图纹理流送性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "texture_streaming",
        "duration": 120,
        "metrics": ["gpu_memory_mb", "disk_read_mbps", "streaming_fps"],
        "category": "level_designer"
    },
    {
        "script_code": "ld_ue_physics",
        "script_name": "UE物理模拟测试",
        "description": "测试物理碰撞模拟性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "physics_sim",
        "duration": 90,
        "metrics": ["cpu_percent", "gpu_percent", "physics_fps"],
        "category": "level_designer"
    },
    {
        "script_code": "ld_ue_worldpartition",
        "script_name": "WorldPartition大地图测试",
        "description": "测试UE5大地图编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "world_partition",
        "duration": 180,
        "metrics": ["cpu_percent", "memory_mb", "gpu_memory_mb", "load_time"],
        "category": "level_designer"
    },
    # TA
    {
        "script_code": "ta_niagara",
        "script_name": "Niagara粒子编辑测试",
        "description": "测试UE5 Niagara粒子系统编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "niagara_edit",
        "duration": 120,
        "metrics": ["gpu_percent", "gpu_memory_mb", "editor_fps"],
        "category": "ta"
    },
    {
        "script_code": "ta_material",
        "script_name": "材质编辑器测试",
        "description": "测试复杂材质Shader编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "material_edit",
        "duration": 90,
        "metrics": ["gpu_percent", "gpu_memory_mb", "compile_time"],
        "category": "ta"
    },
    {
        "script_code": "ta_blueprint_profile",
        "script_name": "蓝图性能分析测试",
        "description": "测试蓝图性能分析工具性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "blueprint_profile",
        "duration": 120,
        "metrics": ["cpu_percent", "memory_mb", "analysis_time"],
        "category": "ta"
    },
    {
        "script_code": "ta_packaging",
        "script_name": "项目打包测试",
        "description": "测试UE项目打包性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "package",
        "duration": 600,
        "metrics": ["cpu_percent", "memory_mb", "disk_write_mbps", "packaging_time"],
        "category": "ta"
    },
    {
        "script_code": "ta_cook",
        "script_name": "资源Cook测试",
        "description": "测试UE资源Cook性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "cook",
        "duration": 600,
        "metrics": ["cpu_percent", "disk_read_mbps", "disk_write_mbps", "cook_time"],
        "category": "ta"
    },
    # 特效
    {
        "script_code": "vfx_vfxgraph",
        "script_name": "VFX Graph编辑测试",
        "description": "测试UE5 VFX Graph实时特效性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "vfx_graph",
        "duration": 120,
        "metrics": ["gpu_percent", "gpu_memory_mb", "vfx_fps"],
        "category": "vfx"
    },
    {
        "script_code": "vfx_cascade",
        "script_name": "Cascade粒子测试",
        "description": "测试旧版粒子系统性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "cascade",
        "duration": 90,
        "metrics": ["gpu_percent", "gpu_memory_mb", "particle_count"],
        "category": "vfx"
    },
    {
        "script_code": "vfx_sequencer",
        "script_name": "Sequencer录制测试",
        "description": "测试视频Sequencer录制性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "sequencer_record",
        "duration": 180,
        "metrics": ["gpu_percent", "disk_write_mbps", "encode_fps"],
        "category": "vfx"
    },
    {
        "script_code": "vfx_scene",
        "script_name": "特效场景编辑测试",
        "description": "测试含大量特效的场景编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "vfx_scene_edit",
        "duration": 120,
        "metrics": ["gpu_percent", "memory_mb", "editor_fps"],
        "category": "vfx"
    },
    # 视频编导
    {
        "script_code": "video_pr_edit",
        "script_name": "Premiere Pro编辑测试",
        "description": "测试Premiere多轨道编辑性能",
        "software": "Premiere Pro",
        "process_name": "Adobe Premiere Pro.exe",
        "scenario": "multi_track_edit",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "preview_fps"],
        "category": "video"
    },
    {
        "script_code": "video_pr_export",
        "script_name": "Premiere渲染导出测试",
        "description": "测试Premiere视频导出性能",
        "software": "Premiere Pro",
        "process_name": "Adobe Premiere Pro.exe",
        "scenario": "export",
        "duration": 300,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "encode_time"],
        "category": "video"
    },
    {
        "script_code": "video_ae_composition",
        "script_name": "After Effects合成测试",
        "description": "测试AE复杂合成效果性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "composition",
        "duration": 180,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "render_time"],
        "category": "video"
    },
    {
        "script_code": "video_ae_render",
        "script_name": "After Effects渲染测试",
        "description": "测试AE多帧渲染性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "render",
        "duration": 600,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "render_time"],
        "category": "video"
    },
    {
        "script_code": "video_ae_preview",
        "script_name": "After Effects特效预览测试",
        "description": "测试AE特效实时预览性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "effect_preview",
        "duration": 90,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "preview_fps"],
        "category": "video"
    },
]


def sync_scripts(db_path="hardware_benchmark.db"):
    """同步脚本到数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_scripts'")
    if not cursor.fetchone():
        print("表 job_scripts 不存在")
        return
    
    # 插入脚本
    count = 0
    for script in SCRIPTS:
        # 检查是否已存在
        cursor.execute("SELECT id FROM job_scripts WHERE script_code = ?", (script["script_code"],))
        if cursor.fetchone():
            print(f"跳过已存在: {script['script_code']}")
            continue
        
        # 构建script_content
        content = {
            "action": "benchmark",
            "benchmark_type": script["script_code"],
            "software": script["software"],
            "process": script["process_name"],
            "scenario": script["scenario"],
            "expected_duration": script["duration"],
            "metrics": script["metrics"]
        }
        
        cursor.execute("""
            INSERT INTO job_scripts 
            (script_name, script_code, script_type, script_content, expected_duration, is_active)
            VALUES (?, ?, 'BENCHMARK', ?, ?, 1)
        """, (
            script["script_name"],
            script["script_code"],
            json.dumps(content, ensure_ascii=False),
            script["duration"]
        ))
        count += 1
        print(f"添加: {script['script_name']} ({script['category']})")
    
    conn.commit()
    conn.close()
    
    print(f"\n共添加 {count} 个测试脚本")


if __name__ == "__main__":
    import os
    db_path = os.path.join(os.path.dirname(__file__), "..", "backend", "hardware_benchmark.db")
    db_path = os.path.abspath(db_path)
    print(f"数据库路径: {db_path}")
    sync_scripts(db_path)
