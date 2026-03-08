/**
 * Data Retention API
 */

import axios from '@/api'

export interface RetentionConfig {
  metrics_retention_days: number
  results_retention_days: number
  audit_logs_retention_days: number
  enable_auto_cleanup: boolean
  cleanup_hour: number
  metrics_collection_interval: number
}

export interface RetentionStats {
  total_metrics: number
  metrics_date_range: {
    oldest: string | null
    newest: string | null
  }
  total_test_results: number
  total_audit_logs: number
  [key: string]: any
}

export interface DataSizes {
  [table: string]: number
}

export interface CleanupResult {
  timestamp: string
  dry_run: boolean
  tasks: {
    table: string
    deleted?: number
    cutoff_date: string
    retention_days?: number
  }[]
  total_deleted: number
}

export interface RetentionOptions {
  metrics_retention_days_options: number[]
  results_retention_days_options: number[]
  audit_logs_retention_days_options: number[]
  collection_interval_options: number[]
  cleanup_hour_options: number[]
}

/**
 * 获取数据保留配置
 */
export function getRetentionConfig() {
  return axios.get<RetentionConfig>('/data-retention/config')
}

/**
 * 获取数据保留统计
 */
export function getRetentionStats() {
  return axios.get<RetentionStats>('/data-retention/stats')
}

/**
 * 获取各表数据大小
 */
export function getDataSizes() {
  return axios.get<DataSizes>('/data-retention/sizes')
}

/**
 * 执行数据清理
 */
export function runCleanup(dryRun: boolean = true) {
  return axios.post<CleanupResult>('/data-retention/cleanup', { dry_run: dryRun })
}

/**
 * 获取可用的保留期限选项
 */
export function getRetentionOptions() {
  return axios.get<RetentionOptions>('/data-retention/retention-options')
}

/**
 * VACUUM 数据库
 */
export function vacuumDatabase() {
  return axios.post<{ success: boolean; message: string }>('/data-retention/vacuum')
}
