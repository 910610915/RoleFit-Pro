#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预设数据初始化脚本
初始化岗位和软件数据
"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.sqlite import Position, TestSoftware, Base
import uuid


def init_preset_data():
    """初始化预设数据"""
    # 使用与后端相同的 SQLite 数据库路径
    db_path = os.path.join(os.path.dirname(__file__), "backend", "hardware_benchmark.db")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # 创建表
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有数据
        existing_positions = session.query(Position).count()
        existing_software = session.query(TestSoftware).count()
        
        if existing_positions > 0 or existing_software > 0:
            print(f"数据库已有数据: {existing_positions} 个岗位, {existing_software} 个软件")
            print("如需重新初始化，请先删除数据库文件。")
            return
        
        # 创建岗位数据
        positions_data = [
            {"name": "UE4开发工程师", "code": "UE4_DEV", "dept": "技术开发部", "description": "负责 Unreal Engine 4 游戏开发"},
            {"name": "UE5开发工程师", "code": "UE5_DEV", "dept": "技术开发部", "description": "负责 Unreal Engine 5 游戏开发"},
            {"name": "Unity开发工程师", "code": "UNITY_DEV", "dept": "技术开发部", "description": "负责 Unity 游戏开发"},
            {"name": "C++后端开发", "code": "CPP_DEV", "dept": "技术开发部", "description": "负责游戏服务器开发"},
            {"name": "C#开发工程师", "code": "CSHARP_DEV", "dept": "技术开发部", "description": "负责工具和编辑器开发"},
            {"name": "3D美术设计师", "code": "3D_ART", "dept": "美术设计部", "description": "负责3D建模和材质制作"},
            {"name": "原画设计师", "code": "CONCEPT_ART", "dept": "美术设计部", "description": "负责游戏概念设计"},
            {"name": "UI设计师", "code": "UI_DESIGN", "dept": "UI设计部", "description": "负责游戏界面设计"},
            {"name": "特效设计师", "code": "VFX", "dept": "特效制作部", "description": "负责游戏特效制作"},
            {"name": "动画师", "code": "ANIM", "dept": "动画制作部", "description": "负责角色和场景动画"},
            {"name": "绑定师", "code": "RIGGING", "dept": "动画制作部", "description": "负责角色骨骼绑定"},
            {"name": "动作捕捉师", "code": "MOCAP", "dept": "动画制作部", "description": "负责动作捕捉数据处理"},
            {"name": "关卡设计师", "code": "LEVEL_DESIGN", "dept": "技术开发部", "description": "负责游戏关卡设计"},
            {"name": "技术美术", "code": "TECH_ART", "dept": "美术设计部", "description": "负责美术工具和流程开发"},
            {"name": "测试工程师", "code": "QA", "dept": "测试QA", "description": "负责游戏功能测试"},
            {"name": "运维工程师", "code": "OPS", "dept": "运维部", "description": "负责服务器运维"},
            {"name": "产品经理", "code": "PM", "dept": "产品部", "description": "负责游戏产品规划"},
            {"name": "项目经理", "code": "PROJECT_MGR", "dept": "项目管理", "description": "负责项目进度管理"},
        ]
        
        print("正在创建岗位数据...")
        for pos in positions_data:
            position = Position(
                id=str(uuid.uuid4()),
                position_name=pos["name"],
                position_code=pos["code"],
                department=pos["dept"],
                description=pos["description"],
                is_active=True
            )
            session.add(position)
        
        session.commit()
        print(f"✓ 已创建 {len(positions_data)} 个岗位")
        
        # 创建软件数据
        software_data = [
            # 开发工具
            {"name": "Unreal Engine 5", "code": "UE5", "vendor": "Epic Games", "category": "DEV", "description": "虚幻引擎5"},
            {"name": "Unreal Engine 4", "code": "UE4", "vendor": "Epic Games", "category": "DEV", "description": "虚幻引擎4"},
            {"name": "Unity 2023", "code": "UNITY2023", "vendor": "Unity Technologies", "category": "DEV", "description": "Unity 2023 LTS"},
            {"name": "Visual Studio 2022", "code": "VS2022", "vendor": "Microsoft", "category": "DEV", "description": "Visual Studio 2022"},
            {"name": "Visual Studio Code", "code": "VSCODE", "vendor": "Microsoft", "category": "DEV", "description": "VS Code 编辑器"},
            {"name": " Rider", "code": "RIDER", "vendor": "JetBrains", "category": "DEV", "description": "JetBrains Rider"},
            {"name": "Perforce Helix Core", "code": "PERFORCE", "vendor": "Perforce", "category": "DEV", "description": "版本控制工具"},
            
            # 美术设计
            {"name": "Photoshop 2024", "code": "PS2024", "vendor": "Adobe", "category": "ART", "description": "Photoshop 2024"},
            {"name": "Illustrator 2024", "code": "AI2024", "vendor": "Adobe", "category": "ART", "description": "Illustrator 2024"},
            {"name": "Substance Painter", "code": "SP", "vendor": "Adobe", "category": "ART", "description": "Substance Painter"},
            {"name": "Substance Designer", "code": "SD", "vendor": "Adobe", "category": "ART", "description": "Substance Designer"},
            {"name": "ZBrush 2024", "code": "ZBRUSH", "vendor": "Maxon", "category": "ART", "description": "ZBrush 2024"},
            {"name": "Maya 2024", "code": "MAYA", "vendor": "Autodesk", "category": "ART", "description": "Autodesk Maya"},
            {"name": "3ds Max 2024", "code": "MAX", "vendor": "Autodesk", "category": "ART", "description": "Autodesk 3ds Max"},
            {"name": "Blender", "code": "BLENDER", "vendor": "Blender Foundation", "category": "ART", "description": "Blender 3D"},
            
            # 动画制作
            {"name": "Maya 2024", "code": "MAYA_ANIM", "vendor": "Autodesk", "category": "ANIM", "description": "Maya 动画"},
            {"name": "MotionBuilder", "code": "MOTIONBUILDER", "vendor": "Autodesk", "category": "ANIM", "description": "MotionBuilder"},
            {"name": "Cascadeur", "code": "CASCADEUR", "vendor": "Autodesk", "category": "ANIM", "description": "Cascadeur 动画"},
            
            # 特效制作
            {"name": "After Effects 2024", "code": "AE2024", "vendor": "Adobe", "category": "VFX", "description": "After Effects"},
            {"name": "Houdini 20", "code": "HOUDINI", "vendor": "SideFX", "category": "VFX", "description": "Houdini FX"},
            {"name": "Nuke 15", "code": "NUKE", "vendor": "Foundry", "category": "VFX", "description": "Nuke 合成"},
            {"name": "Premiere Pro 2024", "code": "PR2024", "vendor": "Adobe", "category": "VFX", "description": "Premiere Pro"},
            
            # UI设计
            {"name": "Figma", "code": "FIGMA", "vendor": "Figma Inc.", "category": "UI", "description": "Figma UI设计"},
            {"name": "Sketch", "code": "SKETCH", "vendor": "Bohemian Coding", "category": "UI", "description": "Sketch UI设计"},
            {"name": "Adobe XD", "code": "XD", "vendor": "Adobe", "category": "UI", "description": "Adobe XD"},
            
            # 工具软件
            {"name": "Notepad++", "code": "NOTEPAD", "vendor": "Notepad++ Team", "category": "TOOL", "description": "文本编辑器"},
            {"name": "Beyond Compare", "code": "BC", "vendor": "Scooter Software", "category": "TOOL", "description": "文件对比工具"},
            {"name": "WinSCP", "code": "WINSCP", "vendor": "WinSCP", "category": "TOOL", "description": "FTP工具"},
            {"name": "Git", "code": "GIT", "vendor": "Git", "category": "TOOL", "description": "版本控制"},
            
            # 办公软件
            {"name": "Microsoft 365", "code": "MS365", "vendor": "Microsoft", "category": "OFFICE", "description": "Office 365"},
            {"name": "Excel", "code": "EXCEL", "vendor": "Microsoft", "category": "OFFICE", "description": "Excel"},
            {"name": "Word", "code": "WORD", "vendor": "Microsoft", "category": "OFFICE", "description": "Word"},
            {"name": "PowerPoint", "code": "PPT", "vendor": "Microsoft", "category": "OFFICE", "description": "PowerPoint"},
            {"name": "钉钉", "code": "DINGTALK", "vendor": "阿里巴巴", "category": "OFFICE", "description": "钉钉"},
            {"name": "企业微信", "code": "WECHAT_WORK", "vendor": "腾讯", "category": "OFFICE", "description": "企业微信"},
        ]
        
        print("正在创建软件数据...")
        for sw in software_data:
            software = TestSoftware(
                id=str(uuid.uuid4()),
                software_name=sw["name"],
                software_code=sw["code"],
                vendor=sw["vendor"],
                category=sw["category"],
                is_active=True
            )
            session.add(software)
        
        session.commit()
        print(f"✓ 已创建 {len(software_data)} 个软件")
        
        print("\n预设数据初始化完成！")
        print(f"总计: {len(positions_data)} 个岗位, {len(software_data)} 个软件")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("硬件性能基准测试系统 - 预设数据初始化")
    print("=" * 50)
    init_preset_data()
