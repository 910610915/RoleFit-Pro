"""
Data analysis and reporting services
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict


class AnalyticsService:
    """Service for data analysis and reporting"""
    
    @staticmethod
    def get_performance_summary(
        results: List[Dict[str, Any]], 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance summary for given time period"""
        if not results:
            return {
                "total_tests": 0,
                "average_score": 0,
                "trend": "stable"
            }
        
        total_tests = len(results)
        
        # Calculate averages
        scores = [r.get("overall_score", 0) for r in results if r.get("overall_score")]
        average_score = sum(scores) / len(scores) if scores else 0
        
        cpu_scores = [r.get("cpu_score", 0) for r in results if r.get("cpu_score")]
        gpu_scores = [r.get("gpu_score", 0) for r in results if r.get("gpu_score")]
        memory_scores = [r.get("memory_score", 0) for r in results if r.get("memory_score")]
        disk_scores = [r.get("disk_score", 0) for r in results if r.get("disk_score")]
        
        # Calculate trend
        trend = "stable"
        if len(scores) >= 10:
            mid = len(scores) // 2
            first_half = scores[:mid]
            second_half = scores[mid:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg > first_avg * 1.05:
                trend = "improving"
            elif second_avg < first_avg * 0.95:
                trend = "declining"
        
        return {
            "total_tests": total_tests,
            "average_score": round(average_score, 2),
            "average_cpu_score": round(sum(cpu_scores) / len(cpu_scores), 2) if cpu_scores else 0,
            "average_gpu_score": round(sum(gpu_scores) / len(gpu_scores), 2) if gpu_scores else 0,
            "average_memory_score": round(sum(memory_scores) / len(memory_scores), 2) if memory_scores else 0,
            "average_disk_score": round(sum(disk_scores) / len(disk_scores), 2) if disk_scores else 0,
            "trend": trend,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0
        }
    
    @staticmethod
    def get_department_analysis(
        results: List[Dict[str, Any]],
        devices: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze performance by department"""
        # Group results by department
        dept_results = defaultdict(list)
        
        for result in results:
            device_id = result.get("device_id")
            # Find device department
            for device in devices:
                if device.get("id") == device_id:
                    dept = device.get("department", "Unknown")
                    dept_results[dept].append(result)
                    break
        
        # Calculate stats per department
        analysis = []
        for dept, dept_results_list in dept_results.items():
            if not dept_results_list:
                continue
                
            scores = [r.get("overall_score", 0) for r in dept_results_list if r.get("overall_score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            passed = sum(1 for r in dept_results_list if r.get("is_standard_met"))
            
            analysis.append({
                "department": dept,
                "total_tests": len(dept_results_list),
                "average_score": round(avg_score, 2),
                "passed_count": passed,
                "compliance_rate": round(passed / len(dept_results_list) * 100, 2) if dept_results_list else 0
            })
        
        return sorted(analysis, key=lambda x: x["average_score"], reverse=True)
    
    @staticmethod
    def get_position_analysis(
        results: List[Dict[str, Any]],
        devices: List[Dict[str, Any]],
        standards: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze compliance by position"""
        # Group by position
        position_results = defaultdict(list)
        
        for result in results:
            device_id = result.get("device_id")
            for device in devices:
                if device.get("id") == device_id:
                    position = device.get("position", "Unknown")
                    position_results[position].append(result)
                    break
        
        analysis = []
        for position, pos_results in position_results.items():
            if not pos_results:
                continue
            
            scores = [r.get("overall_score", 0) for r in pos_results if r.get("overall_score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Find matching standard
            matching_standard = None
            for standard in standards:
                if standard.get("position_code") == position:
                    matching_standard = standard
                    break
            
            # Calculate compliance
            compliant = 0
            for r in pos_results:
                if r.get("is_standard_met"):
                    compliant += 1
            
            analysis.append({
                "position": position,
                "total_devices": len(pos_results),
                "average_score": round(avg_score, 2),
                "compliant_devices": compliant,
                "compliance_rate": round(compliant / len(pos_results) * 100, 2),
                "standard_requirements": matching_standard
            })
        
        return sorted(analysis, key=lambda x: x["compliance_rate"], reverse=True)
    
    @staticmethod
    def get_bottleneck_distribution(
        results: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Get distribution of bottlenecks across all tests"""
        distribution = defaultdict(int)
        
        for result in results:
            bottleneck = result.get("bottleneck_type", "NONE")
            distribution[bottleneck] += 1
        
        return dict(distribution)
    
    @staticmethod
    def get_time_series_data(
        results: List[Dict[str, Any]],
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get time series data for charts"""
        # Group by date
        date_data = defaultdict(lambda: {"scores": [], "count": 0})
        
        for result in results:
            start_time = result.get("start_time")
            if not start_time:
                continue
            
            try:
                if isinstance(start_time, str):
                    date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
                else:
                    date = start_time.date()
            except:
                continue
            
            date_key = date.isoformat()
            score = result.get("overall_score")
            
            if score:
                date_data[date_key]["scores"].append(score)
            date_data[date_key]["count"] += 1
        
        # Convert to list
        time_series = []
        for date_key in sorted(date_data.keys()):
            data = date_data[date_key]
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            
            time_series.append({
                "date": date_key,
                "average_score": round(avg_score, 2),
                "test_count": data["count"]
            })
        
        return time_series[-days:]  # Return last N days
    
    @staticmethod
    def get_device_ranking(
        results: List[Dict[str, Any]],
        devices: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top performing devices"""
        device_scores = defaultdict(list)
        
        for result in results:
            device_id = result.get("device_id")
            score = result.get("overall_score")
            if device_id and score:
                device_scores[device_id].append(score)
        
        # Calculate average scores
        rankings = []
        for device_id, scores in device_scores.items():
            avg_score = sum(scores) / len(scores)
            
            # Find device info
            device_info = None
            for d in devices:
                if d.get("id") == device_id:
                    device_info = d
                    break
            
            if device_info:
                rankings.append({
                    "device_id": device_id,
                    "device_name": device_info.get("device_name", "Unknown"),
                    "department": device_info.get("department", ""),
                    "average_score": round(avg_score, 2),
                    "test_count": len(scores)
                })
        
        # Sort by score
        rankings.sort(key=lambda x: x["average_score"], reverse=True)
        return rankings[:limit]
    
    @staticmethod
    def generate_report(
        results: List[Dict[str, Any]],
        devices: List[Dict[str, Any]],
        standards: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive report"""
        summary = AnalyticsService.get_performance_summary(results)
        dept_analysis = AnalyticsService.get_department_analysis(results, devices)
        position_analysis = AnalyticsService.get_position_analysis(results, devices, standards)
        bottlenecks = AnalyticsService.get_bottleneck_distribution(results)
        time_series = AnalyticsService.get_time_series_data(results)
        rankings = AnalyticsService.get_device_ranking(results, devices)
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "days": 30,
                "total_results": len(results)
            },
            "summary": summary,
            "department_analysis": dept_analysis,
            "position_analysis": position_analysis,
            "bottleneck_distribution": bottlenecks,
            "time_series": time_series,
            "top_devices": rankings
        }


class ReportGenerator:
    """Generate various reports"""
    
    @staticmethod
    def generate_executive_summary(
        results: List[Dict[str, Any]],
        devices: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary text"""
        total_devices = len(devices)
        total_tests = len(results)
        
        passed_tests = sum(1 for r in results if r.get("test_status") == "passed")
        failed_tests = sum(1 for r in results if r.get("test_status") == "failed")
        
        scores = [r.get("overall_score", 0) for r in results if r.get("overall_score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Find top and bottom performers
        rankings = AnalyticsService.get_device_ranking(results, devices, 3)
        
        summary = f"""
# Executive Summary

## Overview
- Total Devices: {total_devices}
- Total Tests: {total_tests}
- Pass Rate: {round(passed_tests / total_tests * 100, 1) if total_tests > 0 else 0}%

## Performance
- Average Score: {round(avg_score, 1)}
- Passed Tests: {passed_tests}
- Failed Tests: {failed_tests}

## Top Performers
"""
        for i, device in enumerate(rankings, 1):
            summary += f"{i}. {device['device_name']} - Score: {device['average_score']}\n"
        
        return summary
    
    @staticmethod
    def generate_device_report(
        device: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate device-specific report"""
        device_results = [r for r in results if r.get("device_id") == device.get("id")]
        
        scores = [r.get("overall_score", 0) for r in device_results if r.get("overall_score")]
        
        return {
            "device": {
                "name": device.get("device_name"),
                "department": device.get("department"),
                "position": device.get("position"),
                "status": device.get("status")
            },
            "hardware": {
                "cpu": device.get("cpu_model"),
                "gpu": device.get("gpu_model"),
                "ram": f"{device.get('ram_total_gb')}GB",
                "storage": device.get("disk_type")
            },
            "test_summary": {
                "total_tests": len(device_results),
                "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "trend": AnalyticsService.calculate_trend(scores)
            },
            "recommendations": []
        }
