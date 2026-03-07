import sys
import os
import json
import uuid
from datetime import datetime

# Add project root to path to import from agent
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "agent"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.sqlite import Base, JobScript, TestSoftware, Position
from app.core.config import settings

# Try to import script definitions
try:
    from test_scripts.script_definitions import ALL_SCRIPTS, SCRIPT_CATEGORIES
    print("成功加载脚本定义")
except ImportError as e:
    try:
        # Fallback for when running from project root
        from agent.test_scripts.script_definitions import ALL_SCRIPTS, SCRIPT_CATEGORIES
        print("成功加载脚本定义 (via agent)")
    except ImportError as e2:
        print(f"无法加载脚本定义: {e}")
        print("请确保 agent/test_scripts/script_definitions.py 存在")
        sys.exit(1)

def init_db():
    engine = create_engine(
        settings.database_url_sync,
        connect_args={"check_same_thread": False}
    )
    Session = sessionmaker(bind=engine)
    return Session()

def add_test_data():
    session = init_db()
    
    print("开始添加测试数据...")
    
    # 1. 添加测试软件
    print("\n[1/3] 检查/添加测试软件...")
    softwares = {
        "Unreal Engine": {"code": "UE", "category": "DEV", "icon": "/software-logos/Unreal Engine.png"},
        "Visual Studio": {"code": "VS", "category": "DEV", "icon": "/software-logos/Visual Studio.png"},
        "Maya": {"code": "MAYA", "category": "ART", "icon": "/software-logos/3Dmax.png"}, # 使用3Dmax图标代替Maya如果没有
        "Blender": {"code": "BLENDER", "category": "ART", "icon": "/software-logos/Blender.png"},
        "ZBrush": {"code": "ZBRUSH", "category": "ART", "icon": "/software-logos/3Dmax.png"},
        "Substance Painter": {"code": "SP", "category": "ART", "icon": "/software-logos/Photoshop.png"},
        "Photoshop": {"code": "PS", "category": "ART", "icon": "/software-logos/Photoshop.png"},
        "Premiere Pro": {"code": "PR", "category": "VIDEO", "icon": "/software-logos/Premiere Pro.png"},
        "After Effects": {"code": "AE", "category": "VFX", "icon": "/software-logos/After Effects.png"},
    }
    
    software_map = {} # name -> id
    
    for name, info in softwares.items():
        # Check by code first (unique constraint)
        sw = session.query(TestSoftware).filter_by(software_code=info["code"]).first()
        if not sw:
            # Check by name just in case
            sw = session.query(TestSoftware).filter_by(software_name=name).first()
            
        if not sw:
            sw = TestSoftware(
                software_name=name,
                software_code=info["code"],
                category=info["category"],
                icon=info["icon"],
                description=f"{name} 标准测试支持",
                software_type="portable",
                detection_method="process"
            )
            session.add(sw)
            session.commit()
            print(f"  + 添加软件: {name}")
        else:
            print(f"  * 已存在: {name} (Code: {info['code']})")
            # Update name if needed or just skip
        software_map[name] = sw.id
        
    # 2. 添加岗位
    print("\n[2/3] 检查/添加岗位...")
    positions = {
        "programmer": "程序开发",
        "artist": "美术设计",
        "level_designer": "关卡设计",
        "ta": "技术美术",
        "vfx": "特效设计",
        "video": "视频编导"
    }
    
    position_map = {} # code -> id
    
    for code, name in positions.items():
        pos = session.query(Position).filter_by(position_code=code).first()
        if not pos:
            pos = Position(
                position_name=name,
                position_code=code,
                department="研发部",
                description=f"{name}岗位",
                is_active=True
            )
            session.add(pos)
            session.commit()
            print(f"  + 添加岗位: {name}")
        else:
            print(f"  * 已存在: {name}")
        position_map[code] = pos.id

    # 3. 添加脚本
    print("\n[3/3] 检查/添加测试脚本...")
    
    count = 0
    for script_code, script_def in ALL_SCRIPTS.items():
        # 检查脚本是否存在
        script = session.query(JobScript).filter_by(script_code=script_code).first()
        
        # 确定关联的软件ID
        sw_name = script_def.get("software")
        sw_id = software_map.get(sw_name)
        
        # 确定关联的岗位IDs
        related_pos_ids = []
        for cat_code, cat_data in SCRIPT_CATEGORIES.items():
            if script_code in cat_data["scripts"]:
                if cat_code in position_map:
                    related_pos_ids.append(position_map[cat_code])
        
        # 构造脚本内容JSON
        content_json = json.dumps(script_def, ensure_ascii=False, indent=2)
        pos_ids_json = json.dumps(related_pos_ids)
        
        if not script:
            script = JobScript(
                script_name=script_def["name"],
                script_code=script_code,
                position_ids=pos_ids_json,
                software_id=sw_id,
                script_type=script_def.get("scenario", "operation").upper(),
                script_content=content_json,
                expected_duration=script_def.get("duration", 300),
                is_active=True
            )
            session.add(script)
            count += 1
            print(f"  + 添加脚本: {script_def['name']}")
        else:
            # 更新现有脚本的内容
            script.script_content = content_json
            script.position_ids = pos_ids_json
            script.software_id = sw_id
            print(f"  * 更新脚本: {script_def['name']}")
            
    session.commit()
    print(f"\n完成! 共添加/更新 {count} 个脚本。")
    session.close()

if __name__ == "__main__":
    add_test_data()
