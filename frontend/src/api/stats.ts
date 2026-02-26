import api from './index'

export interface DashboardSummary {
  total_devices: number
  online_devices: number
  offline_devices: number
  testing_devices: number
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  total_tests: number
  passed_tests: number
  failed_tests: number
  average_score: number
}

export interface DeviceStatusDistribution {
  online: number
  offline: number
  testing: number
  error: number
}

export interface DepartmentDeviceCount {
  department: string
  count: number
  online_count: number
  average_score?: number
}

export interface ScoreTrend {
  date: string
  average_score: number
  test_count: number
}

export interface PositionCompliance {
  position: string
  total_devices: number
  compliant_devices: number
  compliance_rate: number
}

export const statsApi = {
  getDashboard: () => 
    api.get<DashboardSummary>('/stats/dashboard'),
  
  getDeviceStatusDistribution: () => 
    api.get<DeviceStatusDistribution>('/stats/devices/status-distribution'),
  
  getDevicesByDepartment: () => 
    api.get<DepartmentDeviceCount[]>('/stats/devices/by-department'),
  
  getScoreTrend: (days?: number) => 
    api.get<ScoreTrend[]>('/stats/scores/trend', { params: { days } }),
  
  getPositionCompliance: () => 
    api.get<PositionCompliance[]>('/stats/positions/compliance'),
  
  getLeaderboard: (limit?: number) => 
    api.get('/stats/leaderboard/devices', { params: { limit } })
}
