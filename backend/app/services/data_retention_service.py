"""
数据保留策略服务
自动清理过期的性能指标、测试结果和审计日志
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import text

from app.core.config import settings
from app.core.database import sync_engine

logger = logging.getLogger(__name__)


class DataRetentionService:
    """数据保留服务"""

    def __init__(self):
        self.metrics_retention_days = settings.metrics_retention_days
        self.results_retention_days = settings.results_retention_days
        self.audit_logs_retention_days = settings.audit_logs_retention_days

    def get_retention_stats(self) -> Dict[str, Any]:
        """获取数据保留统计"""
        stats = {}

        with sync_engine.connect() as conn:
            # 性能指标统计
            result = conn.execute(
                text("SELECT COUNT(*) as count FROM performance_metrics")
            )
            stats["total_metrics"] = result.fetchone()[0]

            result = conn.execute(
                text("""
                SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest 
                FROM performance_metrics
            """)
            )
            row = result.fetchone()
            stats["metrics_date_range"] = {
                "oldest": row[0].isoformat() if row[0] else None,
                "newest": row[1].isoformat() if row[1] else None,
            }

            # 测试结果统计
            result = conn.execute(text("SELECT COUNT(*) as count FROM test_results"))
            stats["total_test_results"] = result.fetchone()[0]

            # 审计日志统计
            result = conn.execute(text("SELECT COUNT(*) as count FROM audit_logs"))
            stats["total_audit_logs"] = result.fetchone()[0]

            # 其他表统计
            tables = [
                "test_tasks",
                "script_executions",
                "software_metrics",
                "software_benchmarks",
                "performance_alerts",
                "alarms",
            ]

            for table in tables:
                try:
                    result = conn.execute(
                        text(f"SELECT COUNT(*) as count FROM {table}")
                    )
                    stats[f"total_{table}"] = result.fetchone()[0]
                except Exception:
                    pass

        return stats

    def get_data_sizes(self) -> Dict[str, int]:
        """获取各表数据大小(行数)"""
        sizes = {}

        tables = [
            "performance_metrics",
            "test_results",
            "audit_logs",
            "test_tasks",
            "script_executions",
            "software_metrics",
            "software_benchmarks",
            "performance_alerts",
            "alarms",
            "control_commands",
            "ai_analysis_reports",
        ]

        with sync_engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    sizes[table] = result.fetchone()[0]
                except Exception:
                    sizes[table] = 0

        return sizes

    def cleanup_performance_metrics(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的性能指标数据"""
        cutoff_date = datetime.now() - timedelta(days=self.metrics_retention_days)

        with sync_engine.connect() as conn:
            # 先统计要删除的数据量
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM performance_metrics 
                WHERE timestamp < :cutoff
            """),
                {"cutoff": cutoff_date},
            )
            count_to_delete = result.fetchone()[0]

            if dry_run:
                return {
                    "table": "performance_metrics",
                    "will_delete": count_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": self.metrics_retention_days,
                }

            if count_to_delete > 0:
                # 执行删除
                conn.execute(
                    text("""
                    DELETE FROM performance_metrics 
                    WHERE timestamp < :cutoff
                """),
                    {"cutoff": cutoff_date},
                )
                conn.commit()

                # 清理孤立数据
                conn.execute(
                    text("""
                    DELETE FROM performance_metrics 
                    WHERE device_id NOT IN (SELECT id FROM devices)
                """)
                )
                conn.commit()

            return {
                "table": "performance_metrics",
                "deleted": count_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.metrics_retention_days,
            }

    def cleanup_test_results(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的测试结果"""
        cutoff_date = datetime.now() - timedelta(days=self.results_retention_days)

        with sync_engine.connect() as conn:
            # 统计要删除的数据量
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM test_results 
                WHERE created_at < :cutoff
            """),
                {"cutoff": cutoff_date},
            )
            count_to_delete = result.fetchone()[0]

            if dry_run:
                return {
                    "table": "test_results",
                    "will_delete": count_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": self.results_retention_days,
                }

            if count_to_delete > 0:
                conn.execute(
                    text("""
                    DELETE FROM test_results 
                    WHERE created_at < :cutoff
                """),
                    {"cutoff": cutoff_date},
                )
                conn.commit()

            return {
                "table": "test_results",
                "deleted": count_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.results_retention_days,
            }

    def cleanup_audit_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的审计日志"""
        cutoff_date = datetime.now() - timedelta(days=self.audit_logs_retention_days)

        with sync_engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE created_at < :cutoff
            """),
                {"cutoff": cutoff_date},
            )
            count_to_delete = result.fetchone()[0]

            if dry_run:
                return {
                    "table": "audit_logs",
                    "will_delete": count_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": self.audit_logs_retention_days,
                }

            if count_to_delete > 0:
                conn.execute(
                    text("""
                    DELETE FROM audit_logs 
                    WHERE created_at < :cutoff
                """),
                    {"cutoff": cutoff_date},
                )
                conn.commit()

            return {
                "table": "audit_logs",
                "deleted": count_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.audit_logs_retention_days,
            }

    def cleanup_software_metrics(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的软件运行指标"""
        cutoff_date = datetime.now() - timedelta(days=self.metrics_retention_days)

        with sync_engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM software_metrics 
                WHERE timestamp < :cutoff
            """),
                {"cutoff": cutoff_date},
            )
            count_to_delete = result.fetchone()[0]

            if dry_run:
                return {
                    "table": "software_metrics",
                    "will_delete": count_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": self.metrics_retention_days,
                }

            if count_to_delete > 0:
                conn.execute(
                    text("""
                    DELETE FROM software_metrics 
                    WHERE timestamp < :cutoff
                """),
                    {"cutoff": cutoff_date},
                )
                conn.commit()

            return {
                "table": "software_metrics",
                "deleted": count_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.metrics_retention_days,
            }

    def cleanup_old_commands(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的控制命令"""
        cutoff_date = datetime.now() - timedelta(days=30)

        with sync_engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM control_commands 
                WHERE created_at < :cutoff AND status IN ('completed', 'failed')
            """),
                {"cutoff": cutoff_date},
            )
            count_to_delete = result.fetchone()[0]

            if dry_run:
                return {
                    "table": "control_commands",
                    "will_delete": count_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                }

            if count_to_delete > 0:
                conn.execute(
                    text("""
                    DELETE FROM control_commands 
                    WHERE created_at < :cutoff AND status IN ('completed', 'failed')
                """),
                    {"cutoff": cutoff_date},
                )
                conn.commit()

            return {
                "table": "control_commands",
                "deleted": count_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
            }

    def run_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """执行所有清理任务"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "tasks": [],
        }

        # 清理各项数据
        results["tasks"].append(self.cleanup_performance_metrics(dry_run))
        results["tasks"].append(self.cleanup_test_results(dry_run))
        results["tasks"].append(self.cleanup_audit_logs(dry_run))
        results["tasks"].append(self.cleanup_software_metrics(dry_run))
        results["tasks"].append(self.cleanup_old_commands(dry_run))

        # 统计删除总数
        results["total_deleted"] = sum(
            task.get("deleted", task.get("will_delete", 0)) for task in results["tasks"]
        )

        return results

    def vacuum_database(self) -> Dict[str, Any]:
        """VACUUM 数据库以回收空间"""
        try:
            with sync_engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
            return {"success": True, "message": "数据库 VACUUM 完成"}
        except Exception as e:
            logger.error(f"VACUUM failed: {e}")
            return {"success": False, "message": str(e)}


# 全局服务实例
retention_service = DataRetentionService()
