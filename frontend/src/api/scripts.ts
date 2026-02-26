import api from './index'

export interface Script {
  id: string
  script_name: string
  script_code: string
  position_ids?: string[]
  software_id?: string
  script_type?: string
  script_content: string
  expected_duration: number
  is_active: boolean
  created_at: string
}

export interface ScriptListResponse {
  total: number
  page: number
  page_size: number
  items: Script[]
}

export interface ScriptParams {
  page?: number
  page_size?: number
  position_id?: string
  software_id?: string
}

export const scriptApi = {
  list: (params?: ScriptParams) => 
    api.get<ScriptListResponse>('/scripts', { params }),
  
  get: (id: string) => 
    api.get<Script>(`/scripts/${id}`),
  
  create: (data: Partial<Script>) => 
    api.post<Script>('/scripts', data),
  
  update: (id: string, data: Partial<Script>) => 
    api.put<Script>(`/scripts/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/scripts/${id}`)
}
