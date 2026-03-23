/**
 * Prometheus 数据查询 Composable
 * 用于直接查询 Prometheus API 获取监控数据
 */

import { ref } from 'vue'
import axios from 'axios'

const PROMETHEUS_URL = import.meta.env.VITE_PROMETHEUS_URL || 'http://localhost:9090'

export interface MetricPoint {
  timestamp: number
  value: number
}

export interface MetricSeries {
  metric: string
  instance: string
  points: MetricPoint[]
}

export interface GpuMetrics {
  utilization: MetricSeries[]
  temperature: MetricSeries[]
}

export function usePrometheus() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 查询单个指标 (即时查询)
   */
  async function queryMetric(
    query: string,
    time?: string
  ): Promise<MetricSeries[]> {
    loading.value = true
    error.value = null

    try {
      const params: Record<string, string> = { query }
      if (time) params.time = time

      const response = await axios.get(
        `${PROMETHEUS_URL}/api/v1/query`,
        { params }
      )

      if (response.data.status !== 'success') {
        throw new Error(response.data.error || 'Query failed')
      }

      return response.data.data.result.map((item: any) => ({
        metric: item.metric.__name__ || '',
        instance: item.metric.instance || '',
        points: item.values.map(([ts, val]: [number, string]) => ({
          timestamp: ts * 1000,
          value: parseFloat(val)
        }))
      }))
    } catch (e: any) {
      error.value = e.message || 'Failed to query Prometheus'
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 查询指标范围数据
   */
  async function queryRange(
    query: string,
    start: number,
    end: number,
    step = '15s'
  ): Promise<MetricSeries[]> {
    loading.value = true
    error.value = null

    try {
      // Convert to Unix timestamps if needed
      const startTs = typeof start === 'number' && start > 1e12 ? Math.floor(start / 1000) : Math.floor(start)
      const endTs = typeof end === 'number' && end > 1e12 ? Math.floor(end / 1000) : Math.floor(end)

      const response = await axios.get(
        `${PROMETHEUS_URL}/api/v1/query_range`,
        {
          params: { query, start: startTs, end: endTs, step }
        }
      )

      if (response.data.status !== 'success') {
        throw new Error(response.data.error || 'Query failed')
      }

      return response.data.data.result.map((item: any) => ({
        metric: item.metric.__name__ || '',
        instance: item.metric.instance || '',
        points: item.values.map(([ts, val]: [number, string]) => ({
          timestamp: ts * 1000,
          value: parseFloat(val)
        }))
      }))
    } catch (e: any) {
      error.value = e.message || 'Failed to query Prometheus range'
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取 CPU 使用率
   */
  async function getCpuPercent(instance: string, minutes = 60): Promise<MetricSeries[]> {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    const query = `windows_cpu_percent{instance="${instance}"}`
    return queryRange(query, start, end)
  }

  /**
   * 获取 CPU 温度
   */
  async function getCpuTemperature(instance: string, minutes = 60): Promise<MetricSeries[]> {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    const query = `windows_cpu_temperature_celsius{instance="${instance}"}`
    return queryRange(query, start, end)
  }

  /**
   * 获取内存使用率
   */
  async function getMemoryPercent(instance: string, minutes = 60): Promise<MetricSeries[]> {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    const query = `windows_memory_percent{instance="${instance}"}`
    return queryRange(query, start, end)
  }

  /**
   * 获取 GPU 指标
   */
  async function getGpuMetrics(instance: string, minutes = 60): Promise<GpuMetrics> {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    
    const [utilization, temperature] = await Promise.all([
      queryRange(`windows_gpu_percent{instance="${instance}"}`, start, end),
      queryRange(`windows_gpu_temperature_celsius{instance="${instance}"}`, start, end)
    ])

    return { utilization, temperature }
  }

  /**
   * 获取所有 GPU 指标 (多种指标)
   */
  async function getAllGpuMetrics(instance: string, minutes = 60): Promise<GpuMetrics> {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    
    const [utilization, temperature, memory, power] = await Promise.all([
      queryRange(`windows_gpu_percent{instance="${instance}"}`, start, end),
      queryRange(`windows_gpu_temperature_celsius{instance="${instance}"}`, start, end),
      queryRange(`windows_gpu_memory_percent{instance="${instance}"}`, start, end),
      queryRange(`windows_gpu_power_watts{instance="${instance}"}`, start, end)
    ])

    return { utilization, temperature }
  }

  /**
   * 获取当前指标值
   */
  async function getCurrentValue(query: string): Promise<number | null> {
    const results = await queryMetric(query)
    if (results.length > 0 && results[0].points.length > 0) {
      return results[0].points[results[0].points.length - 1].value
    }
    return null
  }

  /**
   * 获取最新指标 (简化版本)
   */
  async function getLatestMetrics(instance: string): Promise<{
    cpu: number | null
    memory: number | null
    gpu: number | null
    gpuTemp: number | null
    cpuTemp: number | null
  }> {
    const [cpu, memory, gpu] = await Promise.all([
      getCurrentValue(`windows_cpu_percent{instance="${instance}"}`),
      getCurrentValue(`windows_memory_percent{instance="${instance}"}`),
      getCurrentValue(`windows_gpu_percent{instance="${instance}"}`)
    ])

    const [gpuTemp, cpuTemp] = await Promise.all([
      getCurrentValue(`windows_gpu_temperature_celsius{instance="${instance}"}`),
      getCurrentValue(`windows_cpu_temperature_celsius{instance="${instance}"}`)
    ])

    return { cpu, memory, gpu, gpuTemp, cpuTemp }
  }

  /**
   * 检查 Prometheus 连接状态
   */
  async function checkStatus(): Promise<boolean> {
    try {
      const response = await axios.get(`${PROMETHEUS_URL}/-/ready`, {
        timeout: 5000
      })
      return response.status === 200
    } catch {
      return false
    }
  }

  return {
    loading,
    error,
    queryMetric,
    queryRange,
    getCpuPercent,
    getCpuTemperature,
    getMemoryPercent,
    getGpuMetrics,
    getAllGpuMetrics,
    getCurrentValue,
    getLatestMetrics,
    checkStatus
  }
}
