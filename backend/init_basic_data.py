"""
初始化基础数据脚本
用于在新环境中初始化脚本和软件数据
从 data/ 目录下的 JSON 文件读取配置
"""

import os
import json
import uuid
from datetime import datetime

from sqlalchemy import select, func
from app.core.database import SyncSessionLocal
from app.models.sqlite import JobScript, TestSoftware, Position


def get_data_path(filename: str) -> str:
    """获取数据文件路径"""
    return os.path.join(os.path.dirname(__file__), "data", filename)


def load_json_data(filename: str) -> dict:
    """从 JSON 文件加载数据"""
    filepath = get_data_path(filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def init_basic_data():
    """
    初始化基础数据（软件和脚本）
    在新环境中运行此函数来创建基础数据
    数据从 data/test_software.json 和 data/job_scripts.json 读取
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

        # ==================== 加载软件数据 ====================
        print("\n[1/2] 加载软件数据...")
        software_data = load_json_data("test_software.json")

        software_map = {}  # software_code -> id

        if software_data and "data" in software_data:
            for sw in software_data["data"]:
                # 检查是否已存在（通过 software_code）
                existing = (
                    session.query(TestSoftware)
                    .filter_by(software_code=sw["software_code"])
                    .first()
                )

                if not existing:
                    sw_obj = TestSoftware(
                        id=sw.get("id", str(uuid.uuid4())),
                        software_name=sw["software_name"],
                        software_code=sw["software_code"],
                        category=sw.get("category"),
                        icon=sw.get("icon"),
                        description=sw.get("description"),
                        software_type=sw.get("software_type", "portable"),
                        detection_method=sw.get("detection_method", "process"),
                        is_active=sw.get("is_active", True),
                        created_at=datetime.now(),
                    )
                    session.add(sw_obj)
                    print(f"  + 添加软件: {sw['software_name']}")
                else:
                    print(f"  * 已存在: {sw['software_name']}")

                software_map[sw["software_code"]] = sw.get("id")

            session.commit()
            print(f"加载了 {len(software_data['data'])} 个软件")
        else:
            print("  警告: 未找到软件数据文件 data/test_software.json")

        # ==================== 加载脚本数据 ====================
        print("\n[2/2] 加载脚本数据...")
        script_data = load_json_data("job_scripts.json")

        if script_data and "data" in script_data:
            for script in script_data["data"]:
                # 检查是否已存在（通过 script_code）
                existing = (
                    session.query(JobScript)
                    .filter_by(script_code=script["script_code"])
                    .first()
                )

                if not existing:
                    # 解析 position_ids（可能是 JSON 字符串或列表）
                    position_ids = script.get("position_ids")
                    if isinstance(position_ids, str):
                        try:
                            position_ids = json.loads(position_ids)
                        except:
                            position_ids = None

                    script_obj = JobScript(
                        id=script.get("id", str(uuid.uuid4())),
                        script_name=script["script_name"],
                        script_code=script["script_code"],
                        software_id=script.get("software_id"),
                        script_type=script.get("script_type"),
                        script_content=script.get("script_content"),
                        expected_duration=script.get("expected_duration", 300),
                        is_active=script.get("is_active", True),
                        created_at=datetime.now(),
                    )
                    session.add(script_obj)
                    print(f"  + 添加脚本: {script['script_name']}")
                else:
                    print(f"  * 已存在: {script['script_name']}")

            session.commit()
            print(f"加载了 {len(script_data['data'])} 个脚本")
        else:
            print("  警告: 未找到脚本数据文件 data/job_scripts.json")

        # ==================== 加载岗位数据 ====================
        print("\n[3/3] 加载岗位数据...")
        position_data = load_json_data("positions.json")

        if position_data and "data" in position_data:
            for pos in position_data["data"]:
                # 检查是否已存在（通过 position_code）
                existing = (
                    session.query(Position)
                    .filter_by(position_code=pos["position_code"])
                    .first()
                )

                if not existing:
                    pos_obj = Position(
                        id=pos.get("id", str(uuid.uuid4())),
                        position_name=pos["position_name"],
                        position_code=pos["position_code"],
                        department=pos.get("department", "研发部"),
                        description=pos.get(
                            "description", f"{pos['position_name']}岗位"
                        ),
                        is_active=pos.get("is_active", True),
                    )
                    session.add(pos_obj)
                    print(f"  + 添加岗位: {pos['position_name']}")
                else:
                    print(f"  * 已存在: {pos['position_name']}")

            session.commit()
            print(f"加载了 {len(position_data['data'])} 个岗位")
        else:
            print("  警告: 未找到岗位数据文件 data/positions.json")

        print("\n基础数据初始化完成！")

    except Exception as e:
        print(f"初始化数据时出错: {e}")
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    init_basic_data()
