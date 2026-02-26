import api from './index'

export interface TestResult {
  id: string
  task_id?: string
  device_id: string
  test_type?: string
  test_status?: string
  start_time: string
  end_time: string
  duration_seconds: number
  overall_score?: number
  cpu_score?: number
  gpu_score?: number
  memory_score?: number
  disk_score?: number
  is_standard_met?: boolean
  standard_id?: string
  fail_reasons?: Record<string, any>
  performance_summary?: Record<string, any>
  bottleneck_type?: string
  bottleneck_detail?: Record<string, any>
  upgrade_suggestion?: Record<string, any>
  result_file_path?: string
  log_file_path?: string
  created_at: string
}

export interface ResultListResponse {
  total: number
  page: number
  page_size: number
  items: TestResult[]
}

export interface ResultParams {
  page?: number
  page_size?: number
  device_id?: string
  task_id?: string
  test_status?: string
  is_standard_met?: boolean
  start_date?: string
  end_date?: string
}

export const resultApi = {
  list: (params?: ResultParams) => 
    api.get<ResultListResponse>('/results', { params }),
  
  get: (id: string) => 
    api.get<TestResult>(`/results/${id}`),
  
  getMetrics: (resultId: string) => 
    api.get<any[]>(`/results/${resultId}/metrics`),
  
  getDeviceStats: (deviceId: string) => 
    api.get(`/results/statistics/device/${deviceId}`),
  
  compareDevices: (deviceIds: string[]) => 
    api.get<any[]>('/results/compare', { params: { device_ids: deviceIds.join(',') } })
}
