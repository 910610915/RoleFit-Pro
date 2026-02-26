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
    api.delete(`/devices/${id}`)
}
