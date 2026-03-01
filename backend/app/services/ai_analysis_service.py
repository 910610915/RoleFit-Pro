"""
AI 分析服务 - 基于 LLM 的性能分析和瓶颈识别
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.services.llm_service import LLMProvider, get_llm_client

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI 性能分析服务"""

    # 系统提示词
    PERFORMANCE_ANALYSIS_SYSTEM_PROMPT = """你是一个专业的硬件性能分析专家，专门分析软件开发人员的工作站性能。
你的分析需要：
1. 识别硬件瓶颈（CPU/GPU/内存/磁盘/IO）
2. 提供具体的升级建议
3. 量化预期改善效果

请用中文回复，保持专业但易懂。"""

    BOTTLENECK_ANALYSIS_PROMPT = """## 设备信息
- CPU: {cpu_model}
- GPU: {gpu_model}
- 显存: {vram_gb:.1f}GB
- 内存: {memory_gb:.1f}GB
- 磁盘: {disk_type}

## 实时监控数据
{cpu_info}
{gpu_info}
{memory_info}
{disk_info}

## 基准测试结果
{benchmark_info}

请分析：
1. 当前系统状态是否存在性能问题？
2. 主要瓶颈是什么？
3. 对于软件 {software_name} 的 {benchmark_type} 任务表现如何？
4. 升级建议（如果有）"""

    UPGRADE_RECOMMENDATION_PROMPT = """## 当前硬件配置
- CPU: {cpu_model} ({cpu_cores}核{threads}线程)
- GPU: {gpu_model} ({vram_gb:.0f}GB)
- 内存: {memory_gb:.1f}GB
- 磁盘: {disk_type} {disk_capacity:.1f}TB

## 岗位需求
- 岗位类型: {position_type}
- 主要工作负载: {workload}

## 性能测试结果
{benchmark_results}

请给出：
1. 硬件达标情况评估
2. 升级优先级建议
3. 具体升级方案和预算估算"""

    def __init__(self, llm_client: Optional[LLMProvider] = None):
        self.llm = llm_client or get_llm_client()

    def analyze_realtime_metrics(
        self, device_info: Dict[str, Any], metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析实时性能指标

        Args:
            device_info: 设备硬件信息
            metrics: 性能指标列表

        Returns:
            分析结果
        """
        if not metrics:
            return {"status": "error", "message": "没有足够的性能数据进行分析"}

        # 计算平均值和峰值
        avg_cpu = sum(m.get("cpu_percent", 0) or 0 for m in metrics) / len(metrics)
        avg_gpu = sum(m.get("gpu_percent", 0) or 0 for m in metrics) / len(metrics)
        avg_memory = sum(m.get("memory_percent", 0) or 0 for m in metrics) / len(
            metrics
        )

        peak_cpu = max((m.get("cpu_percent", 0) or 0 for m in metrics), default=0)
        peak_gpu = max((m.get("gpu_percent", 0) or 0 for m in metrics), default=0)
        peak_memory = max((m.get("memory_percent", 0) or 0 for m in metrics), default=0)

        # 构建分析提示
        prompt = f"""## 设备硬件
- CPU: {device_info.get("cpu_model", "Unknown")}
- GPU: {device_info.get("gpu_model", "Unknown")}
- 内存: {device_info.get("ram_total_gb", 0)}GB

## 性能监控数据 (最近 {len(metrics)} 个采样点)

### CPU
- 平均: {avg_cpu:.1f}%
- 峰值: {peak_cpu:.1f}%

### GPU
- 平均: {avg_gpu:.1f}%
- 峰值: {peak_gpu:.1f}%

### 内存
- 平均: {avg_memory:.1f}%
- 峰值: {peak_memory:.1f}%

请分析是否存在性能瓶颈，给出简短的评估和必要的建议。"""

        try:
            result = self.llm.chat(
                message=prompt,
                system_prompt=self.PERFORMANCE_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1000,
            )

            # 解析判断是否正常
            issues = []
            if avg_cpu > 90:
                issues.append("CPU 使用率过高")
            if peak_cpu > 95:
                issues.append("CPU 峰值接近100%")
            if avg_gpu > 90:
                issues.append("GPU 使用率过高")
            if peak_gpu > 95:
                issues.append("GPU 峰值接近100%")
            if avg_memory > 85:
                issues.append("内存使用率偏高")
            if peak_memory > 95:
                issues.append("内存使用率接近满载")

            return {
                "status": "completed",
                "summary": result.get("content", ""),
                "metrics_summary": {
                    "avg_cpu_percent": round(avg_cpu, 1),
                    "avg_gpu_percent": round(avg_gpu, 1),
                    "avg_memory_percent": round(avg_memory, 1),
                    "peak_cpu_percent": round(peak_cpu, 1),
                    "peak_gpu_percent": round(peak_gpu, 1),
                    "peak_memory_percent": round(peak_memory, 1),
                },
                "issues": issues,
                "model": result.get("model"),
                "usage": result.get("usage"),
            }
        except Exception as e:
            logger.error(f"实时指标分析失败: {e}")
            return {"status": "error", "message": str(e)}

    def analyze_benchmark(
        self, device_info: Dict[str, Any], benchmark: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析基准测试结果

        Args:
            device_info: 设备硬件信息
            benchmark: 基准测试结果

        Returns:
            瓶颈分析和升级建议
        """
        # 构建分析提示
        prompt = f"""## 设备硬件
- CPU: {device_info.get("cpu_model", "Unknown")}
- GPU: {device_info.get("gpu_model", "Unknown")}
- 显存: {device_info.get("gpu_vram_mb", 0) / 1024:.1f}GB
- 内存: {device_info.get("ram_total_gb", 0)}GB
- 磁盘: {device_info.get("disk_type", "Unknown")}

## 基准测试: {benchmark.get("software_code", "Unknown")} - {benchmark.get("benchmark_type", "Unknown")}
- 测试场景: {benchmark.get("test_scene", "N/A")}
- 测试状态: {benchmark.get("status", "Unknown")}

### 得分
- 综合得分: {benchmark.get("score", "N/A")}
- CPU 得分: {benchmark.get("score_cpu", "N/A")}
- GPU 得分: {benchmark.get("score_gpu", "N/A")}
- 内存得分: {benchmark.get("score_memory", "N/A")}
- 磁盘得分: {benchmark.get("score_disk", "N/A")}

### 详细指标
- 平均 FPS: {benchmark.get("avg_fps", "N/A")}
- 渲染时间: {benchmark.get("render_time_seconds", "N/A")}秒
- CPU 峰值: {benchmark.get("peak_cpu_percent", "N/A")}%
- GPU 峰值: {benchmark.get("peak_gpu_percent", "N/A")}%
- 内存峰值: {benchmark.get("peak_memory_mb", "N/A")}MB

请分析：
1. 瓶颈类型 (CPU/GPU/内存/磁盘)
2. 具体问题分析
3. 升级建议（如果有）
4. 预期的性能改善

请以 JSON 格式输出：
{{
  "bottleneck_type": "CPU/GPU/MEMORY/DISK/IO/NONE",
  "analysis": "详细分析",
  "upgrade_suggestion": "升级建议",
  "estimated_improvement": "预期改善"
}}"""

        try:
            result = self.llm.chat(
                message=prompt,
                system_prompt=self.PERFORMANCE_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=1500,
            )

            # 尝试解析 JSON
            try:
                analysis = json.loads(result.get("content", "{}"))
            except:
                # 如果不是 JSON，创建结构化响应
                analysis = {
                    "analysis": result.get("content", ""),
                    "bottleneck_type": "UNKNOWN",
                }

            return {
                "status": "completed",
                "benchmark_id": benchmark.get("id"),
                "bottleneck_type": analysis.get("bottleneck_type", "UNKNOWN"),
                "analysis": analysis.get("analysis", ""),
                "upgrade_suggestion": analysis.get("upgrade_suggestion", ""),
                "estimated_improvement": analysis.get("estimated_improvement", ""),
                "model": result.get("model"),
                "usage": result.get("usage"),
            }
        except Exception as e:
            logger.error(f"基准测试分析失败: {e}")
            return {"status": "error", "message": str(e)}

    def generate_upgrade_recommendation(
        self,
        device_info: Dict[str, Any],
        benchmarks: List[Dict[str, Any]],
        position_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成升级建议

        Args:
            device_info: 设备硬件信息
            benchmarks: 基准测试结果列表
            position_requirements: 岗位需求 (可选)

        Returns:
            升级建议
        """
        # 构建基准测试摘要
        benchmark_summary = []
        for b in benchmarks:
            benchmark_summary.append(
                {
                    "software": b.get("software_code"),
                    "type": b.get("benchmark_type"),
                    "score": b.get("score"),
                    "status": b.get("status"),
                    "avg_cpu": b.get("avg_cpu_percent"),
                    "avg_gpu": b.get("avg_gpu_percent"),
                }
            )

        prompt = f"""## 当前硬件配置
- CPU: {device_info.get("cpu_model", "Unknown")} ({device_info.get("cpu_cores", "?")}核{device_info.get("cpu_threads", "?")}线程)
- GPU: {device_info.get("gpu_model", "Unknown")} ({device_info.get("gpu_vram_mb", 0) / 1024:.0f}GB)
- 内存: {device_info.get("ram_total_gb", 0)}GB
- 磁盘: {device_info.get("disk_type", "Unknown")} {device_info.get("disk_capacity_tb", 0)}TB

## 基准测试结果
{json.dumps(benchmark_summary, indent=2, ensure_ascii=False)}"""

        if position_requirements:
            prompt += f"""

## 目标岗位需求
{json.dumps(position_requirements, indent=2, ensure_ascii=False)}"""

        prompt += """

请作为硬件升级顾问，给出：
1. 当前配置的优缺点
2. 升级优先级（哪些硬件最需要升级）
3. 针对软件开发工作的具体升级方案
4. 预估升级后的效果

请用中文回复，保持专业但易懂。"""

        try:
            result = self.llm.chat(
                message=prompt,
                system_prompt=self.PERFORMANCE_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=2000,
            )

            return {
                "status": "completed",
                "recommendation": result.get("content", ""),
                "model": result.get("model"),
                "usage": result.get("usage"),
            }
        except Exception as e:
            logger.error(f"升级建议生成失败: {e}")
            return {"status": "error", "message": str(e)}

    def analyze_performance_trend(
        self,
        device_id: str,
        metrics_history: List[Dict[str, Any]],
        benchmarks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        分析性能趋势

        Args:
            device_id: 设备ID
            metrics_history: 历史指标数据
            benchmarks: 历史基准测试数据

        Returns:
            趋势分析报告
        """
        if not metrics_history and not benchmarks:
            return {"status": "error", "message": "没有足够的历史数据进行分析"}

        # 提取关键趋势数据
        if metrics_history:
            # 按时间排序
            sorted_metrics = sorted(
                metrics_history, key=lambda x: x.get("timestamp", "")
            )

            # 计算最近24小时 vs 之前24小时的对比
            now = datetime.utcnow()
            day_ago = now - timedelta(hours=24)

            recent = [
                m
                for m in sorted_metrics
                if m.get("timestamp", "") > day_ago.isoformat()
            ]
            older = [
                m
                for m in sorted_metrics
                if m.get("timestamp", "") <= day_ago.isoformat()
                and m.get("timestamp", "") > (day_ago - timedelta(hours=24)).isoformat()
            ]

            trend_data = {
                "recent_count": len(recent),
                "older_count": len(older),
            }

            if recent and older:
                recent_avg_cpu = sum(
                    m.get("cpu_percent", 0) or 0 for m in recent
                ) / len(recent)
                older_avg_cpu = sum(m.get("cpu_percent", 0) or 0 for m in older) / len(
                    older
                )
                trend_data["cpu_trend"] = recent_avg_cpu - older_avg_cpu

                recent_avg_memory = sum(
                    m.get("memory_percent", 0) or 0 for m in recent
                ) / len(recent)
                older_avg_memory = sum(
                    m.get("memory_percent", 0) or 0 for m in older
                ) / len(older)
                trend_data["memory_trend"] = recent_avg_memory - older_avg_memory
        else:
            trend_data = {"recent_count": 0, "older_count": 0}

        # 基准测试趋势
        if benchmarks:
            sorted_benchmarks = sorted(benchmarks, key=lambda x: x.get("timestamp", ""))
            recent_benchmarks = sorted_benchmarks[-5:]  # 最近5个

            benchmark_trend = {
                "recent_count": len(recent_benchmarks),
                "scores": [b.get("score") for b in recent_benchmarks if b.get("score")],
            }
        else:
            benchmark_trend = {"recent_count": 0}

        prompt = f"""## 性能趋势数据

### 实时指标趋势
{json.dumps(trend_data, indent=2, ensure_ascii=False)}

### 基准测试趋势
{json.dumps(benchmark_trend, indent=2, ensure_ascii=False)}

请分析：
1. 性能是否有下降趋势？
2. 是否存在间歇性性能问题？
3. 硬件健康状态评估
4. 维护建议

请用中文简洁回复。"""

        try:
            result = self.llm.chat(
                message=prompt,
                system_prompt=self.PERFORMANCE_ANALYSIS_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1500,
            )

            return {
                "status": "completed",
                "trend_summary": result.get("content", ""),
                "trend_data": trend_data,
                "benchmark_trend": benchmark_trend,
                "model": result.get("model"),
                "usage": result.get("usage"),
            }
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return {"status": "error", "message": str(e)}


# 全局服务实例
def get_ai_analysis_service() -> AIAnalysisService:
    """获取 AI 分析服务实例"""
    return AIAnalysisService()
