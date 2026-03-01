import api from './index'

export interface Device {
  id: string
  device_name: string
  mac_address: string
  ip_address?: string
  hostname?: string
  department?: string
  position?: string
  assigned_to?: string
  notes?: string
  status: string
  last_seen_at?: string
  registered_at: string
  // Hardware info
  cpu_model?: string
  cpu_cores?: number
  cpu_threads?: number
  cpu_base_clock?: number
  gpu_model?: string
  gpu_vram_mb?: number
  gpu_driver_version?: string
  all_gpus?: Array<{ name: string; vram_mb: number; driver_version: string }>
  ram_total_gb?: number
  ram_frequency?: number
  ram_sticks?: number
  all_memory?: Array<{ capacity_mb: number; speed: number; manufacturer: string }>
  disk_model?: string
  disk_capacity_tb?: number
  disk_type?: string
  all_disks?: Array<{ model: string; capacity_tb: number; type: string; interface: string }>
  os_name?: string
  os_version?: string
  os_build?: string
}

export interface DeviceListResponse {
  total: number
  page: number
  page_size: number
  items: Device[]
}

export interface DeviceCreate {
  device_name: string
  mac_address: string
  ip_address?: string
  hostname?: string
  department?: string
  position?: string
  assigned_to?: string
  notes?: string
}

export interface DeviceUpdate {
  device_name?: string
  ip_address?: string
  hostname?: string
  department?: string
  position?: string
  assigned_to?: string
  notes?: string
}

export interface DeviceParams {
  page?: number
  page_size?: number
  status?: string
  department?: string
  position?: string
  keyword?: string
}

// Performance metric types
export interface PerformanceMetric {
  id: string
  device_id: string
  timestamp: string
  cpu_percent?: number
  gpu_percent?: number
  memory_percent?: number
  disk_read_mbps?: number
  disk_write_mbps?: number
  network_sent_mbps?: number
  network_recv_mbps?: number
}

export interface PerformanceMetricResponse {
  total: number
  items: PerformanceMetric[]
}

export interface DeviceStatus {
  device_id: string
  latest_metric?: PerformanceMetric
  pending_alerts_count: number
  recent_benchmarks: any[]
  status: string
}

export interface Benchmark {
  id: string
  device_id: string
  software_code: string
  benchmark_type: string
  timestamp: string
  status: string
  score?: number
}

export interface Task {
  id: string
  task_name: string
  task_type: string
  task_status: string
  created_at: string
}

export const deviceApi = {
  list: (params?: DeviceParams) => 
    api.get<DeviceListResponse>('/devices', { params }),
  
  get: (id: string) => 
    api.get<Device>(`/devices/${id}`),
  
  create: (data: DeviceCreate) => 
    api.post<Device>('/devices', data),
  
  update: (id: string, data: DeviceUpdate) => 
    api.put<Device>(`/devices/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/devices/${id}`),
    
  // Performance metrics
  getMetrics: (deviceId: string, params?: { limit?: number; offset?: number }) =>
    api.get<PerformanceMetricResponse>(`/performance/metrics`, { 
      params: { device_id: deviceId, ...params } 
    }),
    
  getLatestMetric: (deviceId: string) =>
    api.get<PerformanceMetric>(`/performance/metrics/latest`, {
      params: { device_id: deviceId }
    }),
    
  getRealtimeMetrics: (deviceId: string, seconds?: number) =>
    api.get<{ device_id: string; metrics: PerformanceMetric[]; averages: any }>(
      `/performance/metrics/realtime/${deviceId}`,
      { params: { seconds } }
    ),
    
  // Device status
  getStatus: (deviceId: string) =>
    api.get<DeviceStatus>(`/performance/devices/${deviceId}/status`),
    
  // Benchmarks
  getBenchmarks: (params?: { device_id?: string; software_code?: string; limit?: number }) =>
    api.get<{ total: number; items: Benchmark[] }>('/performance/benchmarks', { params }),
    
  // Tasks
  getTasks: (params?: { page?: number; page_size?: number; task_status?: string }) =>
    api.get<{ total: number; items: Task[] }>('/tasks', { params }),
    
  createTask: (data: any) =>
    api.post<Task>('/tasks', data)
}

// 兼容导出
export const getDevices = deviceApi.list
export const getDeviceById = deviceApi.get
export const getDeviceStatus = deviceApi.getStatus
export const getPerformanceMetrics = deviceApi.getMetrics
export const getBenchmarks = deviceApi.getBenchmarks
export const getTasks = deviceApi.getTasks
export const createTask = deviceApi.createTask
