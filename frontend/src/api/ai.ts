import api from './index'

export interface AIAnalysisRequest {
  device_id?: string
  query?: string
  analysis_type: string
  seconds?: number
}

export interface AIAnalysisResponse {
  id?: string
  device_id: string
  analysis_type: string
  title: string
  summary?: string
  details?: any
  conclusions?: string
  recommendations?: string
  status?: string
}

export interface AIAnalysisReport {
  id: string
  device_id: string
  analysis_type: string
  title: string
  summary?: string
  conclusions?: string
  recommendations?: string
  created_at: string
}

export const aiApi = {
  // Analyze realtime metrics
  analyzeMetrics: (deviceId: string, seconds?: number) =>
    api.post<AIAnalysisResponse>('/ai/analyze/metrics', null, {
      params: { device_id: deviceId, seconds }
    }),
    
  // Analyze benchmark results
  analyzeBenchmark: (benchmarkId: string) =>
    api.post<AIAnalysisResponse>('/ai/analyze/benchmark', null, {
      params: { benchmark_id: benchmarkId }
    }),
    
  // General AI query
  analyze: (data: AIAnalysisRequest) =>
    api.post<AIAnalysisResponse>('/ai/analyze', data),
    
  // Get analysis reports
  getReports: (params?: { device_id?: string; analysis_type?: string; limit?: number }) =>
    api.get<{ total: number; items: AIAnalysisReport[] }>('/ai/reports', { params }),
    
  // Get single report
  getReport: (id: string) =>
    api.get<AIAnalysisReport>(`/ai/reports/${id}`)
}

// 兼容导出
export const aiAnalyze = aiApi.analyze
export const aiAnalyzeMetrics = aiApi.analyzeMetrics
export const aiGetReports = aiApi.getReports
