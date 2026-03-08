from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timedelta
import json
import time

from app.core.database import get_db_sync
from app.models.sqlite import (
    Device,
    PerformanceMetric,
    SoftwareBenchmark,
    AIAnalysisReport,
    PositionStandard,
)
from app.schemas.performance import AIAnalysisRequest, AIAnalysisResponse, AIAnalysisMetricsRequest
from app.services.ai_analysis_service import AIAnalysisService
from app.services.llm_service import LLMProvider

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


def device_to_info(device: Device) -> dict:
    """转换设备信息为字典"""
    return {
        "id": device.id,
        "device_name": device.device_name,
        "cpu_model": device.cpu_model,
        "cpu_cores": device.cpu_cores,
        "cpu_threads": device.cpu_threads,
        "gpu_model": device.gpu_model,
        "gpu_vram_mb": device.gpu_vram_mb,
        "ram_total_gb": device.ram_total_gb,
        "disk_type": device.disk_type,
        "disk_capacity_tb": device.disk_capacity_tb,
    }


@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze_general(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db_sync),
):
    """
    通用 AI 分析接口 - 支持自然语言查询
    """
    # 初始化 LLM Provider
    llm_provider = None
    if request.api_key:
        llm_provider = LLMProvider(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url
        )

    analysis_service = AIAnalysisService(llm_client=llm_provider)

    # 获取用户查询
    query = request.query

    if not query:
        return {"status": "error", "summary": "请提供查询内容"}

    # 先尝试直接查询设备列表（用于"列出设备"等场景）
    if any(
        keyword in query
        for keyword in ["列出", "列表", "显示设备", "所有设备", "设备列表", "查看设备"]
    ):
        try:
            devices_result = db.execute(select(Device).limit(50))
            devices = devices_result.scalars().all()

            if devices:
                device_list = []
                for d in devices:
                    status = "🟢 在线" if d.status == "online" else "🔴 离线"
                    device_list.append(
                        f"• {d.device_name} - {status}\n  CPU: {d.cpu_model or '未知'}\n  GPU: {d.gpu_model or '未知'}"
                    )

                return {
                    "status": "completed",
                    "summary": "📊 设备列表：\n\n" + "\n\n".join(device_list),
                    "device_id": request.device_id or "",
                    "analysis_type": request.analysis_type or "general",
                    "title": "设备列表查询",
                }
        except Exception as e:
            pass  # 如果失败，继续走AI分析

    # 获取设备信息（如果提供了 device_id）
    device_info = None
    if request.device_id:
        device_result = db.execute(select(Device).where(Device.id == request.device_id))
        device = device_result.scalar_one_or_none()
        if device:
            device_info = device_to_info(device)

    try:
        # 构建提示词，让 AI 回答问题时使用中文并保持换行
        prompt = f"""你是一个专业的硬件性能分析助手。请用中文回答。

用户问题：{query}

{"设备信息：" + str(device_info) if device_info else ""}

重要要求：
1. 使用换行符(\\n)来分隔不同内容
2. 不要使用表格格式，使用列表和项目符号
3. 保持简洁清晰的格式"""

        result = analysis_service.llm.chat(
            message=prompt,
            system_prompt="你是一个专业的硬件性能分析助手。请用中文回答，使用换行符来分隔内容，不要使用表格。",
            temperature=0.7,
            max_tokens=1500,
        )

        summary = result.get("content", "")

        return {
            "status": "completed",
            "summary": summary,
            "device_id": request.device_id or "",
            "analysis_type": request.analysis_type or "general",
            "title": f"AI 分析 - {query[:30]}",
            "report_id": f"adhoc-{int(time.time())}"
        }

    except Exception as e:
        return {"status": "error", "summary": f"分析失败：{str(e)}", "report_id": "error", "title": "Error"}


@router.post("/analyze/metrics", response_model=AIAnalysisResponse)
def analyze_realtime_metrics(
    request: AIAnalysisMetricsRequest,
    db: Session = Depends(get_db_sync),
):
    """
    分析设备实时性能指标
    """
    device_id = request.device_id
    seconds = request.seconds

    # 获取设备信息
    device_result = db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 获取最近 N 秒的性能指标
    since = datetime.utcnow() - timedelta(seconds=seconds)
    metrics_result = db.execute(
        select(PerformanceMetric)
        .where(PerformanceMetric.device_id == device_id)
        .where(PerformanceMetric.timestamp >= since)
        .order_by(PerformanceMetric.timestamp.asc())
    )
    metrics = metrics_result.scalars().all()

    if not metrics:
        raise HTTPException(
            status_code=404, detail="No metrics found for the specified time range"
        )

    # 转换为字典列表
    metrics_data = []
    for m in metrics:
        metrics_data.append(
            {
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "cpu_percent": m.cpu_percent,
                "gpu_percent": m.gpu_percent,
                "memory_percent": m.memory_percent,
                "cpu_temperature": m.cpu_temperature,
                "gpu_temperature": m.gpu_temperature,
            }
        )

    # 初始化 LLM Provider
    llm_provider = None
    if request.api_key:
        llm_provider = LLMProvider(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url
        )
    
    # 调用 AI 分析服务
    analysis_service = AIAnalysisService(llm_client=llm_provider)
    device_info = device_to_info(device)
    result = analysis_service.analyze_realtime_metrics(device_info, metrics_data)

    # 保存分析报告
    if result.get("status") == "completed":
        report = AIAnalysisReport(
            device_id=device_id,
            analysis_type="realtime_metrics",
            title=f"实时性能分析 - {device.device_name}",
            summary=result.get("summary", ""),
            details=json.dumps(
                {
                    "metrics_summary": result.get("metrics_summary"),
                    "issues": result.get("issues"),
                },
                ensure_ascii=False,
            ),
            status="completed",
            model_used=result.get("model"),
            analysis_duration_ms=int(
                result.get("usage", {}).get("total_tokens", 0) * 10
            ),  # 估算
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "report_id": report.id,
            "status": result.get("status"),
            "summary": result.get("summary"),
            "conclusions": result.get("summary"),
            "recommendations": "\n".join(result.get("issues", [])),
            "details": result.get("metrics_summary"),
        }

    raise HTTPException(
        status_code=500, detail=result.get("message", "Analysis failed")
    )


@router.post("/analyze/benchmark/{benchmark_id}", response_model=AIAnalysisResponse)
def analyze_benchmark_result(benchmark_id: str, db: Session = Depends(get_db_sync)):
    """
    分析基准测试结果
    """
    # 获取基准测试记录
    benchmark_result = db.execute(
        select(SoftwareBenchmark).where(SoftwareBenchmark.id == benchmark_id)
    )
    benchmark = benchmark_result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # 获取设备信息
    device_result = db.execute(select(Device).where(Device.id == benchmark.device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 调用 AI 分析服务
    analysis_service = AIAnalysisService()
    device_info = device_to_info(device)
    benchmark_data = {
        "id": benchmark.id,
        "software_code": benchmark.software_code,
        "benchmark_type": benchmark.benchmark_type,
        "test_scene": benchmark.test_scene,
        "score": benchmark.score,
        "score_cpu": benchmark.score_cpu,
        "score_gpu": benchmark.score_gpu,
        "score_memory": benchmark.score_memory,
        "score_disk": benchmark.score_disk,
        "avg_fps": benchmark.avg_fps,
        "render_time_seconds": benchmark.render_time_seconds,
        "peak_cpu_percent": benchmark.peak_cpu_percent,
        "peak_gpu_percent": benchmark.peak_gpu_percent,
        "peak_memory_mb": benchmark.peak_memory_mb,
        "status": benchmark.status,
    }

    result = analysis_service.analyze_benchmark(device_info, benchmark_data)

    # 保存分析报告
    if result.get("status") == "completed":
        report = AIAnalysisReport(
            device_id=benchmark.device_id,
            analysis_type="benchmark",
            title=f"基准测试分析 - {benchmark.software_code}",
            summary=result.get("analysis", ""),
            details=json.dumps(
                {
                    "benchmark_id": benchmark_id,
                    "bottleneck_type": result.get("bottleneck_type"),
                    "upgrade_suggestion": result.get("upgrade_suggestion"),
                    "estimated_improvement": result.get("estimated_improvement"),
                },
                ensure_ascii=False,
            ),
            conclusions=result.get("analysis", ""),
            recommendations=result.get("upgrade_suggestion", ""),
            related_benchmarks=json.dumps([benchmark_id]),
            status="completed",
            model_used=result.get("model"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # 更新基准测试记录的瓶颈分析
        benchmark.bottleneck_type = result.get("bottleneck_type")
        benchmark.bottleneck_detail = result.get("analysis", "")
        benchmark.upgrade_suggestion = result.get("upgrade_suggestion", "")
        db.commit()

        return {
            "report_id": report.id,
            "status": result.get("status"),
            "summary": result.get("analysis"),
            "conclusions": result.get("analysis"),
            "recommendations": result.get("upgrade_suggestion"),
            "details": {
                "bottleneck_type": result.get("bottleneck_type"),
                "estimated_improvement": result.get("estimated_improvement"),
            },
        }

    raise HTTPException(
        status_code=500, detail=result.get("message", "Analysis failed")
    )


@router.post("/analyze/upgrade", response_model=AIAnalysisResponse)
def analyze_upgrade_recommendation(
    device_id: str,
    position_id: Optional[str] = Query(None, description="岗位ID，用于匹配岗位需求"),
    db: Session = Depends(get_db_sync),
):
    """
    生成硬件升级建议
    """
    # 获取设备信息
    device_result = db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 获取最近的基准测试结果
    benchmarks_result = db.execute(
        select(SoftwareBenchmark)
        .where(SoftwareBenchmark.device_id == device_id)
        .order_by(SoftwareBenchmark.timestamp.desc())
        .limit(10)
    )
    benchmarks = benchmarks_result.scalars().all()

    benchmarks_data = []
    for b in benchmarks:
        benchmarks_data.append(
            {
                "id": b.id,
                "software_code": b.software_code,
                "benchmark_type": b.benchmark_type,
                "score": b.score,
                "status": b.status,
                "avg_cpu_percent": b.avg_cpu_percent,
                "avg_gpu_percent": b.avg_gpu_percent,
            }
        )

    # 获取岗位需求（如果有）
    position_requirements = None
    if position_id:
        position_result = db.execute(
            select(PositionStandard).where(PositionStandard.id == position_id)
        )
        position = position_result.scalar_one_or_none()
        if position:
            position_requirements = {
                "position_name": position.position_name,
                "cpu_min_cores": position.cpu_min_cores,
                "cpu_min_threads": position.cpu_min_threads,
                "ram_min_gb": position.ram_min_gb,
                "gpu_min_vram_mb": position.gpu_min_vram_mb,
                "viewport_fps_min": position.viewport_fps_min,
                "render_time_max_seconds": position.render_time_max_seconds,
            }

    # 调用 AI 分析服务
    analysis_service = AIAnalysisService()
    device_info = device_to_info(device)
    result = analysis_service.generate_upgrade_recommendation(
        device_info, benchmarks_data, position_requirements
    )

    # 保存分析报告
    if result.get("status") == "completed":
        report = AIAnalysisReport(
            device_id=device_id,
            analysis_type="upgrade_recommendation",
            title=f"硬件升级建议 - {device.device_name}",
            summary=result.get("recommendation", ""),
            details=json.dumps(
                {
                    "benchmarks_count": len(benchmarks_data),
                    "position_requirements": position_requirements,
                },
                ensure_ascii=False,
            ),
            conclusions=result.get("recommendation", ""),
            recommendations=result.get("recommendation", ""),
            related_benchmarks=json.dumps([b.id for b in benchmarks]),
            status="completed",
            model_used=result.get("model"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "report_id": report.id,
            "status": result.get("status"),
            "summary": result.get("recommendation"),
            "conclusions": result.get("recommendation"),
            "recommendations": result.get("recommendation"),
            "details": {
                "benchmarks_analyzed": len(benchmarks_data),
                "position_requirements_matched": position_id is not None,
            },
        }

    raise HTTPException(
        status_code=500, detail=result.get("message", "Analysis failed")
    )


@router.post("/analyze/trend", response_model=AIAnalysisResponse)
def analyze_performance_trend(
    device_id: str,
    hours: int = Query(72, ge=24, le=720, description="分析最近N小时的数据"),
    db: Session = Depends(get_db_sync),
):
    """
    分析性能趋势
    """
    # 获取设备信息
    device_result = db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 获取历史性能指标
    since = datetime.utcnow() - timedelta(hours=hours)
    metrics_result = db.execute(
        select(PerformanceMetric)
        .where(PerformanceMetric.device_id == device_id)
        .where(PerformanceMetric.timestamp >= since)
        .order_by(PerformanceMetric.timestamp.asc())
    )
    metrics = metrics_result.scalars().all()

    metrics_history = []
    for m in metrics:
        metrics_history.append(
            {
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "cpu_percent": m.cpu_percent,
                "gpu_percent": m.gpu_percent,
                "memory_percent": m.memory_percent,
            }
        )

    # 获取历史基准测试
    benchmarks_result = db.execute(
        select(SoftwareBenchmark)
        .where(SoftwareBenchmark.device_id == device_id)
        .where(SoftwareBenchmark.timestamp >= since)
        .order_by(SoftwareBenchmark.timestamp.desc())
    )
    benchmarks = benchmarks_result.scalars().all()

    benchmarks_data = []
    for b in benchmarks:
        benchmarks_data.append(
            {
                "id": b.id,
                "timestamp": b.timestamp.isoformat() if b.timestamp else None,
                "software_code": b.software_code,
                "benchmark_type": b.benchmark_type,
                "score": b.score,
            }
        )

    if not metrics_history and not benchmarks_data:
        raise HTTPException(
            status_code=404,
            detail="No historical data found for the specified time range",
        )

    # 调用 AI 分析服务
    analysis_service = AIAnalysisService()
    result = analysis_service.analyze_performance_trend(
        device_id, metrics_history, benchmarks_data
    )

    # 保存分析报告
    if result.get("status") == "completed":
        report = AIAnalysisReport(
            device_id=device_id,
            analysis_type="performance_trend",
            title=f"性能趋势分析 - {device.device_name}",
            summary=result.get("trend_summary", ""),
            details=json.dumps(
                {
                    "trend_data": result.get("trend_data"),
                    "benchmark_trend": result.get("benchmark_trend"),
                },
                ensure_ascii=False,
            ),
            conclusions=result.get("trend_summary", ""),
            related_metrics=json.dumps(
                [
                    m.get("timestamp")
                    for m in metrics_history[:: max(1, len(metrics_history) // 100)]
                ]
            ),
            related_benchmarks=json.dumps([b.get("id") for b in benchmarks_data]),
            status="completed",
            model_used=result.get("model"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "report_id": report.id,
            "status": result.get("status"),
            "summary": result.get("trend_summary"),
            "conclusions": result.get("trend_summary"),
            "recommendations": "",
            "details": result.get("trend_data"),
        }

    raise HTTPException(
        status_code=500, detail=result.get("message", "Analysis failed")
    )


@router.get("/reports", response_model=dict)
def get_analysis_reports(
    device_id: Optional[str] = Query(None),
    analysis_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_sync),
):
    """获取分析报告列表"""
    query = select(AIAnalysisReport)

    if device_id:
        query = query.where(AIAnalysisReport.device_id == device_id)
    if analysis_type:
        query = query.where(AIAnalysisReport.analysis_type == analysis_type)

    # 获取总数
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # 获取分页结果
    query = (
        query.order_by(AIAnalysisReport.created_at.desc()).offset(offset).limit(limit)
    )
    reports = db.execute(query).scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "device_id": r.device_id,
                "analysis_type": r.analysis_type,
                "title": r.title,
                "summary": r.summary,
                "status": r.status,
                "model_used": r.model_used,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


@router.get("/reports/{report_id}", response_model=dict)
def get_analysis_report(report_id: str, db: Session = Depends(get_db_sync)):
    """获取分析报告详情"""
    result = db.execute(
        select(AIAnalysisReport).where(AIAnalysisReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "device_id": report.device_id,
        "analysis_type": report.analysis_type,
        "title": report.title,
        "summary": report.summary,
        "details": report.details,
        "conclusions": report.conclusions,
        "recommendations": report.recommendations,
        "status": report.status,
        "related_metrics": report.related_metrics,
        "related_benchmarks": report.related_benchmarks,
        "model_used": report.model_used,
        "analysis_duration_ms": report.analysis_duration_ms,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }
