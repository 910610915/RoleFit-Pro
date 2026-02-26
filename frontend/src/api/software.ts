import api from './index'

export interface Software {
  id: string
  software_name: string
  software_code: string
  vendor?: string
  category?: string
  version?: string
  description?: string
  launch_params?: string
  icon?: string  // 图标路径
  
  // 安装配置
  software_type?: 'installer' | 'portable'
  package_format?: 'exe' | 'msi' | 'zip' | 'rar' | '7z'
  storage_path?: string
  target_install_path?: string
  subfolder_name?: string
  silent_install_cmd?: string
  main_exe_relative_path?: string
  
  // 检测配置
  detection_method?: 'file' | 'process' | 'registry'
  detection_path?: string
  detection_keyword?: string
  
  // 状态
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface SoftwareListResponse {
  total: number
  page: number
  page_size: number
  items: Software[]
}

export interface SoftwareParams {
  page?: number
  page_size?: number
  category?: string
}

export const softwareApi = {
  list: (params?: SoftwareParams) => 
    api.get<SoftwareListResponse>('/software', { params }),
  
  get: (id: string) => 
    api.get<Software>(`/software/${id}`),
  
  create: (data: Partial<Software>) => 
    api.post<Software>('/software', data),
  
  update: (id: string, data: Partial<Software>) => 
    api.put<Software>(`/software/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/software/${id}`)
}
