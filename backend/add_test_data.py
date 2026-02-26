"""
添加测试数据脚本
"""
import sys
import os
import json
import io
import sys

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid
import random

def add_test_data():
    """添加测试数据"""
    
    db_path = os.path.join(os.path.dirname(__file__), "hardware_benchmark.db")
    database_url = f"sqlite:///{db_path}"
    
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    from app.models.sqlite import Device, TestTask, TestResult, PositionStandard
    
    print("正在添加测试数据...")
    
    # 添加岗位标准
    standards = [
        PositionStandard(
            id=str(uuid.uuid4()),
            position_name='开发工程师',
            position_code='DEV',
            description='游戏开发工程师岗位硬件标准',
            cpu_min_cores=8,
            cpu_min_threads=16,
            cpu_min_score=5000,
            ram_min_gb=32,
            gpu_min_vram_mb=8192,
            gpu_min_score=8000,
            is_active=True
        ),
        PositionStandard(
            id=str(uuid.uuid4()),
            position_name='UI设计师',
            position_code='DESIGN',
            description='UI设计师岗位硬件标准',
            cpu_min_cores=6,
            cpu_min_threads=12,
            cpu_min_score=4000,
            ram_min_gb=16,
            gpu_min_vram_mb=4096,
            gpu_min_score=5000,
            is_active=True
        ),
        PositionStandard(
            id=str(uuid.uuid4()),
            position_name='QA工程师',
            position_code='QA',
            description='QA测试工程师岗位硬件标准',
            cpu_min_cores=4,
            cpu_min_threads=8,
            cpu_min_score=3000,
            ram_min_gb=16,
            gpu_min_vram_mb=2048,
            gpu_min_score=3000,
            is_active=True
        ),
        PositionStandard(
            id=str(uuid.uuid4()),
            position_name='运维工程师',
            position_code='OPS',
            description='运维工程师岗位硬件标准',
            cpu_min_cores=4,
            cpu_min_threads=8,
            cpu_min_score=3000,
            ram_min_gb=16,
            gpu_min_vram_mb=0,
            gpu_min_score=0,
            is_active=True
        )
    ]
    
    for s in standards:
        existing = session.query(PositionStandard).filter(PositionStandard.position_code == s.position_code).first()
        if not existing:
            session.add(s)
    
    print(f"[OK] 添加了 {len(standards)} 个岗位标准")
    
    # 添加设备
    devices_data = [
        {
            'device_name': 'DEV-PC-001',
            'mac_address': '00:11:22:33:44:01',
            'ip_address': '192.168.1.101',
            'hostname': 'dev-pc-001',
            'department': '开发部',
            'position': '开发工程师',
            'status': 'online',
            'cpu_model': 'Intel Core i9-13900K',
            'cpu_cores': 24,
            'cpu_threads': 32,
            'cpu_base_clock': 3.0,
            'gpu_model': 'NVIDIA RTX 4090',
            'gpu_vram_mb': 24576,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 64,
            'ram_frequency': 5600,
            'disk_model': 'Samsung 990 Pro',
            'disk_capacity_tb': 2,
            'disk_type': 'NVMe',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow()
        },
        {
            'device_name': 'DEV-PC-002',
            'mac_address': '00:11:22:33:44:02',
            'ip_address': '192.168.1.102',
            'hostname': 'dev-pc-002',
            'department': '开发部',
            'position': '开发工程师',
            'status': 'online',
            'cpu_model': 'AMD Ryzen 9 7950X',
            'cpu_cores': 16,
            'cpu_threads': 32,
            'cpu_base_clock': 4.5,
            'gpu_model': 'NVIDIA RTX 4080',
            'gpu_vram_mb': 16384,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 32,
            'ram_frequency': 5200,
            'disk_model': 'WD Black SN850X',
            'disk_capacity_tb': 2,
            'disk_type': 'NVMe',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow() - timedelta(minutes=5)
        },
        {
            'device_name': 'DESIGN-PC-001',
            'mac_address': '00:11:22:33:44:03',
            'ip_address': '192.168.1.201',
            'hostname': 'design-pc-001',
            'department': '设计部',
            'position': 'UI设计师',
            'status': 'online',
            'cpu_model': 'Intel Core i7-13700K',
            'cpu_cores': 16,
            'cpu_threads': 24,
            'cpu_base_clock': 3.4,
            'gpu_model': 'NVIDIA RTX 4070 Ti',
            'gpu_vram_mb': 12288,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 32,
            'ram_frequency': 4800,
            'disk_model': 'Samsung 980 Pro',
            'disk_capacity_tb': 1,
            'disk_type': 'NVMe',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow() - timedelta(minutes=10)
        },
        {
            'device_name': 'DESIGN-PC-002',
            'mac_address': '00:11:22:33:44:04',
            'ip_address': '192.168.1.202',
            'hostname': 'design-pc-002',
            'department': '设计部',
            'position': 'UI设计师',
            'status': 'offline',
            'cpu_model': 'AMD Ryzen 7 7800X3D',
            'cpu_cores': 8,
            'cpu_threads': 16,
            'cpu_base_clock': 4.2,
            'gpu_model': 'NVIDIA RTX 4060 Ti',
            'gpu_vram_mb': 8192,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 16,
            'ram_frequency': 4800,
            'disk_model': 'WD Black SN770',
            'disk_capacity_tb': 1,
            'disk_type': 'NVMe',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'device_name': 'QA-PC-001',
            'mac_address': '00:11:22:33:44:05',
            'ip_address': '192.168.1.301',
            'hostname': 'qa-pc-001',
            'department': '测试部',
            'position': 'QA工程师',
            'status': 'online',
            'cpu_model': 'Intel Core i5-13600K',
            'cpu_cores': 14,
            'cpu_threads': 20,
            'cpu_base_clock': 3.5,
            'gpu_model': 'NVIDIA RTX 3060',
            'gpu_vram_mb': 12288,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 16,
            'ram_frequency': 3200,
            'disk_model': 'Samsung 970 EVO Plus',
            'disk_capacity_tb': 1,
            'disk_type': 'NVMe',
            'os_name': 'Windows 10',
            'os_version': '22H2',
            'last_seen_at': datetime.utcnow() - timedelta(minutes=30)
        },
        {
            'device_name': 'QA-PC-002',
            'mac_address': '00:11:22:33:44:06',
            'ip_address': '192.168.1.302',
            'hostname': 'qa-pc-002',
            'department': '测试部',
            'position': 'QA工程师',
            'status': 'testing',
            'cpu_model': 'AMD Ryzen 5 7600X',
            'cpu_cores': 6,
            'cpu_threads': 12,
            'cpu_base_clock': 4.7,
            'gpu_model': 'NVIDIA RTX 3060 Ti',
            'gpu_vram_mb': 8192,
            'gpu_driver_version': '535.154',
            'ram_total_gb': 16,
            'ram_frequency': 4800,
            'disk_model': 'Crucial P5 Plus',
            'disk_capacity_tb': 1,
            'disk_type': 'NVMe',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow()
        },
        {
            'device_name': 'OPS-PC-001',
            'mac_address': '00:11:22:33:44:07',
            'ip_address': '192.168.1.401',
            'hostname': 'ops-pc-001',
            'department': '运维部',
            'position': '运维工程师',
            'status': 'online',
            'cpu_model': 'Intel Core i3-13100',
            'cpu_cores': 4,
            'cpu_threads': 8,
            'cpu_base_clock': 3.5,
            'gpu_model': 'Intel UHD Graphics 770',
            'gpu_vram_mb': 0,
            'gpu_driver_version': '31.0.101.4030',
            'ram_total_gb': 16,
            'ram_frequency': 3200,
            'disk_model': 'Kingston A400',
            'disk_capacity_tb': 0.5,
            'disk_type': 'SSD',
            'os_name': 'Windows 11',
            'os_version': '23H2',
            'last_seen_at': datetime.utcnow() - timedelta(hours=1)
        },
    ]
    
    devices = []
    for d in devices_data:
        existing = session.query(Device).filter(Device.mac_address == d['mac_address']).first()
        if not existing:
            device = Device(
                id=str(uuid.uuid4()),
                **d
            )
            session.add(device)
            devices.append(device)
        else:
            devices.append(existing)
    
    print(f"[OK] 添加了 {len(devices)} 个设备")
    
    # 添加测试任务
    tasks_data = [
        {
            'task_name': '每日全员硬件巡检',
            'task_type': 'full',
            'task_status': 'completed',
            'target_departments': json.dumps(['开发部', '设计部', '测试部', '运维部'])
        },
        {
            'task_name': '开发部设备性能评估',
            'task_type': 'benchmark',
            'task_status': 'completed',
            'target_departments': json.dumps(['开发部'])
        },
        {
            'task_name': '设计部GPU测试',
            'task_type': 'benchmark',
            'task_status': 'running',
            'target_departments': json.dumps(['设计部'])
        },
        {
            'task_name': '新设备入库检测',
            'task_type': 'benchmark',
            'task_status': 'pending',
            'target_departments': json.dumps([])
        },
    ]
    
    tasks = []
    for i, t in enumerate(tasks_data):
        task = TestTask(
            id=str(uuid.uuid4()),
            **t,
            created_at=datetime.utcnow() - timedelta(days=len(tasks_data)-i),
            started_at=datetime.utcnow() - timedelta(days=len(tasks_data)-i-1) if t['task_status'] in ['completed', 'running'] else None,
            completed_at=datetime.utcnow() - timedelta(hours=2) if t['task_status'] == 'completed' else None
        )
        session.add(task)
        tasks.append(task)
    
    print(f"[OK] 添加了 {len(tasks)} 个测试任务")
    
    # 添加测试结果
    results_data = []
    for device in devices[:5]:  # 只为前5个设备添加结果
        for i in range(3):  # 每个设备3条结果
            days_ago = i * 7 + random.randint(0, 3)
            score = random.randint(60, 100)
            
            result = TestResult(
                id=str(uuid.uuid4()),
                device_id=device.id,
                task_id=tasks[i % len(tasks)].id if i < len(tasks) else None,
                test_type='full' if i == 0 else 'benchmark',
                test_status='passed' if score >= 70 else 'failed',
                start_time=datetime.utcnow() - timedelta(days=days_ago),
                end_time=datetime.utcnow() - timedelta(days=days_ago, hours=-1),
                duration_seconds=random.randint(600, 3600),
                overall_score=float(score),
                cpu_score=float(random.randint(60, 100)),
                gpu_score=float(random.randint(50, 100)),
                memory_score=float(random.randint(70, 100)),
                disk_score=float(random.randint(60, 100)),
                is_standard_met=score >= 70,
                performance_summary=json.dumps({
                    'cpu_usage_avg': random.randint(20, 80),
                    'gpu_usage_avg': random.randint(30, 90),
                    'memory_usage_avg': random.randint(40, 70)
                })
            )
            session.add(result)
            results_data.append(result)
    
    print(f"[OK] 添加了 {len(results_data)} 条测试结果")
    
    session.commit()
    session.close()
    
    print("\n测试数据添加完成!")
    print("\n数据概览:")
    print("  - 设备: 7台 (在线5台，离线1台，测试中1台)")
    print("  - 任务: 4个 (已完成2个，运行中1个，待执行1个)")
    print(f"  - 结果: {len(results_data)} 条")
    print("  - 标准: 4 个岗位标准")


if __name__ == "__main__":
    add_test_data()
