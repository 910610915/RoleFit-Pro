# 游戏公司各岗位测试脚本定义
# 包含：脚本ID、名称、描述、测试场景、指标采集、所需参数

# ============================================
# 脚本参数说明
# ============================================
# required_params: 运行脚本时必须提供的参数
# optional_params: 可选的参数
# file_extensions: 支持的文件类型

# ============================================
# 1. 程序开发测试脚本
# ============================================

PROGRAMMER_SCRIPTS = {
    # UE引擎/项目编译
    "prog_ue_compile": {
        "name": "UE项目编译测试",
        "description": "测试UE5项目完整编译性能，包括C++和蓝图",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "compile",
        "duration": 300,  # 5分钟超时
        "required_params": ["project_path"],  # 需要 .uproject 文件路径
        "optional_params": {
            "target": "Development",  # Build target
            "configuration": "VS"  # Solution configuration
        },
        "metrics": ["cpu_percent", "memory_mb", "disk_write_mbps", "compile_time"],
        "steps": [
            "打开UE5项目",
            "执行完整编译(Build -> Build.cs)",
            "等待编译完成",
            "记录编译时间和资源使用"
        ],
        "notes": "需要提供 .uproject 文件路径"
    },
    
    # VS项目编译
    "prog_vs_build": {
        "name": "Visual Studio编译测试",
        "description": "测试VS2022解决方案编译性能",
        "software": "Visual Studio",
        "process_name": "devenv.exe",
        "scenario": "build",
        "duration": 180,
        "required_params": ["project_path"],  # 需要 .sln 文件路径
        "optional_params": {
            "configuration": "Release",  # Debug/Release
            "platform": "x64"  # x86/x64/AnyCPU
        },
        "metrics": ["cpu_percent", "memory_mb", "compile_time"],
        "steps": [
            "打开VS解决方案",
            "执行完整编译",
            "记录编译时间和资源使用"
        ],
        "notes": "需要提供 .sln 解决方案文件路径"
    },
    
    # Shader编译
    "prog_shader_compile": {
        "name": "Shader编译测试",
        "description": "测试UE材质/Shader首次编译性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "shader_compile",
        "duration": 120,
        "required_params": ["project_path"],
        "metrics": ["cpu_percent", "gpu_percent", "gpu_memory_mb", "compile_time"],
        "steps": [
            "打开UE项目",
            "创建一个复杂材质",
            "应用到场景中触发Shader编译",
            "记录编译时间"
        ],
        "notes": "需要提供 .uproject 文件路径"
    },
    
    # HotReload热重载
    "prog_hot_reload": {
        "name": "HotReload测试",
        "description": "测试代码热重载性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "hot_reload",
        "duration": 60,
        "required_params": ["project_path"],
        "metrics": ["cpu_percent", "memory_mb", "reload_time"],
        "steps": [
            "打开UE项目",
            "修改C++代码",
            "触发热重载",
            "记录重载时间"
        ]
    },
    
    # 调试模式
    "prog_debug": {
        "name": "调试模式测试",
        "description": "测试VS调试模式性能",
        "software": "Visual Studio",
        "process_name": "devenv.exe",
        "scenario": "debug",
        "duration": 90,
        "required_params": ["project_path"],
        "metrics": ["cpu_percent", "memory_mb"],
        "steps": [
            "打开项目",
            "附加到UE调试",
            "设置断点",
            "触发断点"
        ]
    },
    
    # HotReload热重载
    "prog_hot_reload": {
        "name": "HotReload测试",
        "description": "测试代码热重载性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "hot_reload",
        "duration": 60,
        "metrics": ["cpu_percent", "memory_mb", "reload_time"],
        "steps": [
            "打开UE项目",
            "修改C++代码",
            "触发热重载",
            "记录重载时间"
        ]
    },
    
    # 调试模式
    "prog_debug": {
        "name": "调试模式测试",
        "description": "测试VS调试模式性能",
        "software": "Visual Studio",
        "process_name": "devenv.exe",
        "scenario": "debug",
        "duration": 90,
        "metrics": ["cpu_percent", "memory_mb"],
        "steps": [
            "打开项目",
            "附加到UE调试",
            "设置断点",
            "触发断点"
        ]
    }
}

# ============================================
# 2. 美术测试脚本
# ============================================

ARTIST_SCRIPTS = {
    # Maya场景编辑
    "art_maya_scene": {
        "name": "Maya场景编辑测试",
        "description": "测试Maya复杂场景viewport操作性能",
        "software": "Maya",
        "process_name": "maya.exe",
        "scenario": "scene_edit",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "viewport_fps"],
        "steps": [
            "打开Maya",
            "加载复杂场景(100万面+)",
            "进行viewport旋转/缩放操作",
            "记录帧率和资源使用"
        ]
    },
    
    # Blender建模
    "art_blender_model": {
        "name": "Blender建模测试",
        "description": "测试Blender多边形建模性能",
        "software": "Blender",
        "process_name": "blender.exe",
        "scenario": "modeling",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "viewport_fps"],
        "steps": [
            "打开Blender",
            "创建高面数模型",
            "进行编辑操作",
            "记录帧率"
        ]
    },
    
    # ZBrush雕刻
    "art_zbrush_sculpt": {
        "name": "ZBrush雕刻测试",
        "description": "测试ZBrush高精度模型雕刻性能",
        "software": "ZBrush",
        "process_name": "ZBrush.exe",
        "scenario": "sculpt",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb"],
        "steps": [
            "打开ZBrush",
            "加载高分辨率模型",
            "进行雕刻操作",
            "记录资源使用"
        ]
    },
    
    # Substance纹理
    "art_substance_paint": {
        "name": "Substance纹理制作测试",
        "description": "测试Substance Painter纹理处理性能",
        "software": "Substance Painter",
        "process_name": "Adobe Substance 3D Painter.exe",
        "scenario": "texture_paint",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "gpu_memory_mb"],
        "steps": [
            "打开Substance Painter",
            "加载4K纹理项目",
            "执行滤镜操作",
            "记录资源使用"
        ]
    },
    
    # Photoshop大图处理
    "art_ps_large": {
        "name": "Photoshop大图测试",
        "description": "测试Photoshop处理大尺寸图像性能",
        "software": "Photoshop",
        "process_name": "Photoshop.exe",
        "scenario": "large_image",
        "duration": 90,
        "metrics": ["cpu_percent", "memory_mb", "gpu_memory_mb", "operation_time"],
        "steps": [
            "打开Photoshop",
            "加载500MB+PSD文件",
            "执行滤镜/变换操作",
            "记录操作时间和资源"
        ]
    },
    
    # Maya动画播放
    "art_maya_playback": {
        "name": "Maya动画播放测试",
        "description": "测试Maya复杂动画播放流畅度",
        "software": "Maya",
        "process_name": "maya.exe",
        "scenario": "animation_playback",
        "duration": 60,
        "metrics": ["gpu_percent", "memory_mb", "playback_fps"],
        "steps": [
            "打开Maya",
            "加载动画场景",
            "播放动画",
            "记录帧率"
        ]
    }
}

# ============================================
# 3. 地编测试脚本
# ============================================

LEVEL_DESIGNER_SCRIPTS = {
    # UE关卡编辑
    "ld_ue_level": {
        "name": "UE关卡编辑测试",
        "description": "测试UE5大场景关卡编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "level_edit",
        "duration": 180,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "gpu_memory_mb", "editor_fps"],
        "steps": [
            "打开UE关卡(1000+Actor)",
            "进行viewport操作",
            "批量编辑Actor",
            "记录编辑器帧率"
        ]
    },
    
    # 光照构建
    "ld_ue_lighting": {
        "name": "UE光照烘焙测试",
        "description": "测试UE5光照构建性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "light_build",
        "duration": 600,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "build_time"],
        "steps": [
            "打开关卡",
            "配置光源",
            "执行光照构建",
            "记录构建时间"
        ]
    },
    
    # NavMesh构建
    "ld_ue_navmesh": {
        "name": "NavMesh构建测试",
        "description": "测试导航网格生成性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "navmesh_build",
        "duration": 300,
        "metrics": ["cpu_percent", "memory_mb", "build_time"],
        "steps": [
            "打开关卡",
            "配置Navigation Mesh",
            "执行构建",
            "记录构建时间"
        ]
    },
    
    # 贴图流送
    "ld_ue_streaming": {
        "name": "UE纹理流送测试",
        "description": "测试大地图纹理流送性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "texture_streaming",
        "duration": 120,
        "metrics": ["gpu_memory_mb", "disk_read_mbps", "streaming_fps"],
        "steps": [
            "打开大地图关卡",
            "快速移动视角",
            "触发纹理流送",
            "记录显存和帧率"
        ]
    },
    
    # 物理模拟
    "ld_ue_physics": {
        "name": "UE物理模拟测试",
        "description": "测试物理碰撞模拟性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "physics_sim",
        "duration": 90,
        "metrics": ["cpu_percent", "gpu_percent", "physics_fps"],
        "steps": [
            "打开含物理场景",
            "运行PIE",
            "观察物理模拟",
            "记录帧率"
        ]
    },
    
    # WorldPartition大地图
    "ld_ue_worldpartition": {
        "name": "WorldPartition大地图测试",
        "description": "测试UE5大地图编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "world_partition",
        "duration": 180,
        "metrics": ["cpu_percent", "memory_mb", "gpu_memory_mb", "load_time"],
        "steps": [
            "打开WorldPartition地图",
            "加载多个区域",
            "执行编辑操作",
            "记录加载时间和资源"
        ]
    }
}

# ============================================
# 4. TA测试脚本
# ============================================

TA_SCRIPTS = {
    # Niagara粒子编辑
    "ta_niagara": {
        "name": "Niagara粒子编辑测试",
        "description": "测试UE5 Niagara粒子系统编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "niagara_edit",
        "duration": 120,
        "metrics": ["gpu_percent", "gpu_memory_mb", "editor_fps"],
        "steps": [
            "打开Niagara系统",
            "编辑复杂粒子效果",
            "预览效果",
            "记录GPU使用"
        ]
    },
    
    # Material编辑
    "ta_material": {
        "name": "材质编辑器测试",
        "description": "测试复杂材质Shader编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "material_edit",
        "duration": 90,
        "metrics": ["gpu_percent", "gpu_memory_mb", "compile_time"],
        "steps": [
            "打开材质编辑器",
            "创建复杂材质(100+节点)",
            "编译材质",
            "记录编译时间和GPU"
        ]
    },
    
    # 蓝图优化/分析
    "ta_blueprint_profile": {
        "name": "蓝图性能分析测试",
        "description": "测试蓝图性能分析工具性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "blueprint_profile",
        "duration": 120,
        "metrics": ["cpu_percent", "memory_mb", "analysis_time"],
        "steps": [
            "打开蓝图",
            "执行性能分析",
            "查看分析结果",
            "记录分析时间"
        ]
    },
    
    # 项目打包
    "ta_packaging": {
        "name": "项目打包测试",
        "description": "测试UE项目打包性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "package",
        "duration": 600,
        "metrics": ["cpu_percent", "memory_mb", "disk_write_mbps", "packaging_time"],
        "steps": [
            "打开项目",
            "执行Pak打包",
            "等待打包完成",
            "记录打包时间"
        ]
    },
    
    # 资源Cook
    "ta_cook": {
        "name": "资源Cook测试",
        "description": "测试UE资源Cook性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "cook",
        "duration": 600,
        "metrics": ["cpu_percent", "disk_read_mbps", "disk_write_mbps", "cook_time"],
        "steps": [
            "打开项目",
            "执行资源Cook",
            "等待Cook完成",
            "记录Cook时间"
        ]
    }
}

# ============================================
# 5. 特效测试脚本
# ============================================

VFX_SCRIPTS = {
    # VFX Graph
    "vfx_vfxgraph": {
        "name": "VFX Graph编辑测试",
        "description": "测试UE5 VFX Graph实时特效性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "vfx_graph",
        "duration": 120,
        "metrics": ["gpu_percent", "gpu_memory_mb", "vfx_fps"],
        "steps": [
            "打开VFX Graph",
            "编辑复杂特效",
            "预览特效",
            "记录GPU和帧率"
        ]
    },
    
    # Cascade粒子
    "vfx_cascade": {
        "name": "Cascade粒子测试",
        "description": "测试旧版粒子系统性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "cascade",
        "duration": 90,
        "metrics": ["gpu_percent", "gpu_memory_mb", "particle_count"],
        "steps": [
            "打开Cascade",
            "创建大量粒子效果",
            "预览效果",
            "记录GPU使用"
        ]
    },
    
    # Sequencer录制
    "vfx_sequencer": {
        "name": "Sequencer录制测试",
        "description": "测试视频Sequencer录制性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "sequencer_record",
        "duration": 180,
        "metrics": ["gpu_percent", "disk_write_mbps", "encode_fps"],
        "steps": [
            "打开Sequencer",
            "设置录制",
            "开始录制视频",
            "记录录制帧率"
        ]
    },
    
    # 特效场景编辑
    "vfx_scene": {
        "name": "特效场景编辑测试",
        "description": "测试含大量特效的场景编辑性能",
        "software": "Unreal Engine",
        "process_name": "UnrealEditor.exe",
        "scenario": "vfx_scene_edit",
        "duration": 120,
        "metrics": ["gpu_percent", "memory_mb", "editor_fps"],
        "steps": [
            "打开特效场景",
            "进行编辑操作",
            "预览特效",
            "记录帧率"
        ]
    }
}

# ============================================
# 6. 视频编导测试脚本
# ============================================

VIDEO_SCRIPTS = {
    # Premiere Pro编辑
    "video_pr_edit": {
        "name": "Premiere Pro编辑测试",
        "description": "测试Premiere多轨道编辑性能",
        "software": "Premiere Pro",
        "process_name": "Adobe Premiere Pro.exe",
        "scenario": "multi_track_edit",
        "duration": 120,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "preview_fps"],
        "steps": [
            "打开Premiere",
            "加载多轨道项目",
            "播放预览",
            "记录预览帧率"
        ]
    },
    
    # Premiere渲染导出
    "video_pr_export": {
        "name": "Premiere渲染导出测试",
        "description": "测试Premiere视频导出性能",
        "software": "Premiere Pro",
        "process_name": "Adobe Premiere Pro.exe",
        "scenario": "export",
        "duration": 300,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "encode_time"],
        "steps": [
            "打开项目",
            "执行视频导出",
            "等待导出完成",
            "记录导出时间"
        ]
    },
    
    # After Effects合成
    "video_ae_composition": {
        "name": "After Effects合成测试",
        "description": "测试AE复杂合成效果性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "composition",
        "duration": 180,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "render_time"],
        "steps": [
            "打开AE",
            "加载复杂合成",
            "执行预览渲染",
            "记录渲染时间"
        ]
    },
    
    # After Effects渲染
    "video_ae_render": {
        "name": "After Effects渲染测试",
        "description": "测试AE多帧渲染性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "render",
        "duration": 600,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "render_time"],
        "steps": [
            "打开项目",
            "执行多帧渲染",
            "等待渲染完成",
            "记录渲染时间"
        ]
    },
    
    # AE特效预览
    "video_ae_preview": {
        "name": "After Effects特效预览测试",
        "description": "测试AE特效实时预览性能",
        "software": "After Effects",
        "process_name": "AfterFX.exe",
        "scenario": "effect_preview",
        "duration": 90,
        "metrics": ["cpu_percent", "gpu_percent", "memory_mb", "preview_fps"],
        "steps": [
            "打开AE",
            "应用复杂特效",
            "播放预览",
            "记录预览帧率"
        ]
    }
}

# ============================================
# 汇总所有脚本
# ============================================

ALL_SCRIPTS = {
    **PROGRAMMER_SCRIPTS,
    **ARTIST_SCRIPTS,
    **LEVEL_DESIGNER_SCRIPTS,
    **TA_SCRIPTS,
    **VFX_SCRIPTS,
    **VIDEO_SCRIPTS
}

# 脚本分类索引
SCRIPT_CATEGORIES = {
    "programmer": {
        "name": "程序开发",
        "scripts": list(PROGRAMMER_SCRIPTS.keys())
    },
    "artist": {
        "name": "美术",
        "scripts": list(ARTIST_SCRIPTS.keys())
    },
    "level_designer": {
        "name": "地编",
        "scripts": list(LEVEL_DESIGNER_SCRIPTS.keys())
    },
    "ta": {
        "name": "TA技术美术",
        "scripts": list(TA_SCRIPTS.keys())
    },
    "vfx": {
        "name": "特效",
        "scripts": list(VFX_SCRIPTS.keys())
    },
    "video": {
        "name": "视频编导",
        "scripts": list(VIDEO_SCRIPTS.keys())
    }
}
