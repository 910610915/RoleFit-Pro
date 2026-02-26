"""
添加更多测试结果数据以展示图表效果
"""
import sys
import os
import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid
import random

def add_more_results():
    """添加更多测试结果数据"""
    
    db_path = os.path.join(os.path.dirname(__file__), "hardware_benchmark.db")
    database_url = f"sqlite:///{db_path}"
    
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    from app.models.sqlite import Device, TestResult
    
    # 获取所有设备
    devices = session.query(Device).all()
    
    print(f"Found {len(devices)} devices")
    
    # 为每个设备添加30天的测试历史数据
    total_added = 0
    
    for device in devices:
        # 根据设备类型生成不同的分数范围
        if 'DEV' in device.device_name:
            # 开发设备 - 高性能
            base_score = random.randint(75, 95)
        elif 'DESIGN' in device.device_name:
            # 设计设备 - 中高性能
            base_score = random.randint(65, 90)
        elif 'QA' in device.device_name:
            # QA设备 - 中等性能
            base_score = random.randint(55, 80)
        else:
            # 运维设备 - 基础性能
            base_score = random.randint(40, 65)
        
        # 添加过去30天的数据
        for day_offset in range(30):
            # 分数有一些随机波动
            score_variation = random.randint(-10, 10)
            overall_score = max(0, min(100, base_score + score_variation))
            
            # CPU/GPU/内存/磁盘分数
            cpu_score = max(0, min(100, overall_score + random.randint(-15, 15)))
            gpu_score = max(0, min(100, overall_score + random.randint(-15, 15)))
            memory_score = max(0, min(100, overall_score + random.randint(-10, 10)))
            disk_score = max(0, min(100, overall_score + random.randint(-10, 10)))
            
            # 判断是否通过
            is_passed = overall_score >= 60
            
            # 瓶颈类型
            bottleneck_types = [None, 'CPU', 'GPU', 'MEMORY', 'DISK']
            bottleneck = random.choice(bottleneck_types) if not is_passed else None
            
            test_time = datetime.utcnow() - timedelta(days=day_offset)
            duration = random.randint(300, 3600)
            
            result = TestResult(
                id=str(uuid.uuid4()),
                device_id=device.id,
                test_type=random.choice(['full', 'benchmark', 'simulation']),
                test_status='passed' if is_passed else 'failed',
                start_time=test_time,
                end_time=test_time + timedelta(seconds=duration),
                duration_seconds=duration,
                overall_score=float(overall_score),
                cpu_score=float(cpu_score),
                gpu_score=float(gpu_score),
                memory_score=float(memory_score),
                disk_score=float(disk_score),
                is_standard_met=is_passed,
                bottleneck_type=bottleneck,
                performance_summary=json.dumps({
                    'cpu_usage_avg': random.randint(20, 90),
                    'gpu_usage_avg': random.randint(20, 95),
                    'memory_usage_avg': random.randint(30, 85),
                    'disk_usage_avg': random.randint(10, 70)
                })
            )
            session.add(result)
            total_added += 1
    
    session.commit()
    session.close()
    
    print(f"[OK] Added {total_added} test result records")
    print("\nNow the dashboard charts should show 30 days of historical data!")

if __name__ == "__main__":
    add_more_results()
