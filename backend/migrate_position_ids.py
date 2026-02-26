"""
添加 position_ids 列到 job_scripts 表
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'hardware_benchmark.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查列是否存在
cursor.execute("PRAGMA table_info(job_scripts)")
columns = [col[1] for col in cursor.fetchall()]

if 'position_ids' not in columns:
    print("添加 position_ids 列...")
    cursor.execute("ALTER TABLE job_scripts ADD COLUMN position_ids TEXT")
    conn.commit()
    print("完成！")
else:
    print("列已存在，无需修改")

conn.close()
