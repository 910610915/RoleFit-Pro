import api from './index'

export interface TestTask {
  id: string
  task_name: string
  task_type: string
  task_status: string
  target_device_ids: string[]
  target_departments: string[]
  target_positions: string[]
  test_script_id?: string
  test_duration_seconds?: number
  sample_interval_ms: number
  assigned_agent_id?: string
  started_at?: string
  completed_at?: string
  schedule_type?: string
  scheduled_at?: string
  cron_expression?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  total: number
  page: number
  page_size: number
  items: TestTask[]
}

export interface TaskCreate {
  task_name: string
  task_type: string
  target_device_ids?: string[]
  target_departments?: string[]
  target_positions?: string[]
  test_script_id?: string
  test_duration_seconds?: number
  sample_interval_ms?: number
  schedule_type?: string
  scheduled_at?: string
  cron_expression?: string
}

export interface TaskUpdate {
  task_name?: string
  task_status?: string
  target_device_ids?: string[]
  test_duration_seconds?: number
}

export interface TaskParams {
  page?: number
  page_size?: number
  status?: string
  task_type?: string
  creator_id?: string
}

export const taskApi = {
  list: (params?: TaskParams) => 
    api.get<TaskListResponse>('/tasks', { params }),
  
  get: (id: string) => 
    api.get<TestTask>(`/tasks/${id}`),
  
  create: (data: TaskCreate) => 
    api.post<TestTask>('/tasks', data),
  
  update: (id: string, data: TaskUpdate) => 
    api.put<TestTask>(`/tasks/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/tasks/${id}`),
  
  execute: (id: string, device_ids: string[]) => 
    api.post<TestTask>(`/tasks/${id}/execute`, { device_ids }),
  
  cancel: (id: string, reason?: string) => 
    api.post<TestTask>(`/tasks/${id}/cancel`, { reason })
}
