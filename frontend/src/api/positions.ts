import api from './index'

export interface Position {
  id: string
  position_name: string
  position_code: string
  department?: string
  description?: string
  is_active: boolean
  created_at: string
}

export interface PositionListResponse {
  total: number
  page: number
  page_size: number
  items: Position[]
}

export interface PositionParams {
  page?: number
  page_size?: number
  department?: string
}

export const positionApi = {
  list: (params?: PositionParams) => 
    api.get<PositionListResponse>('/positions', { params }),
  
  get: (id: string) => 
    api.get<Position>(`/positions/${id}`),
  
  create: (data: Partial<Position>) => 
    api.post<Position>('/positions', data),
  
  update: (id: string, data: Partial<Position>) => 
    api.put<Position>(`/positions/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/positions/${id}`)
}
