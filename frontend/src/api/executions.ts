import api from './index'

export interface Execution {
  id: string
  task_id?: string
  script_id?: string
  device_id?: string
  start_time: string
  end_time?: string
  duration_seconds?: number
  exit_code: number
  error_message?: string
  created_at: string
}

export interface ExecutionListResponse {
  total: number
  page: number
  page_size: number
  items: Execution[]
}

export interface ExecutionParams {
  page?: number
  page_size?: number
  task_id?: string
  script_id?: string
  device_id?: string
}

export const executionApi = {
  list: (params?: ExecutionParams) => 
    api.get<ExecutionListResponse>('/executions', { params }),
  
  get: (id: string) => 
    api.get<Execution>(`/executions/${id}`),
  
  create: (data: Partial<Execution>) => 
    api.post<Execution>('/executions', data),
  
  update: (id: string, data: Partial<Execution>) => 
    api.put<Execution>(`/executions/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/executions/${id}`)
}

// Agent API (for internal use)
export const agentApi = {
  getOnlineDevices: () => 
    api.get('/agent/devices/online'),
  
  getPendingTasks: (deviceId: string) => 
    api.get('/agent/tasks/pending', { params: { device_id: deviceId } }),
  
  startExecution: (scriptId: string, deviceId: string, taskId?: string) => 
    api.post('/agent/executions/start', null, { params: { script_id: scriptId, device_id: deviceId, task_id: taskId } }),
  
  completeExecution: (executionId: string, exitCode: number, errorMessage?: string) => 
    api.put(`/agent/executions/${executionId}/complete`, null, { params: { exit_code: exitCode, error_message: errorMessage } }),
  
  submitMetrics: (executionId: string, metrics: any[]) => 
    api.post(`/agent/executions/${executionId}/metrics`, metrics)
}
