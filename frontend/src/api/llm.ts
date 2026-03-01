/**
 * LLM API - AI 大模型接口
 */

import axios from './index'

// ================================================
// Types
// ================================================

export interface LLMProvider {
  id: string
  name: string
  default_model: string
  free: boolean
  models: string[]
}

export interface ChatRequest {
  message: string
  provider?: string
  model?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
}

export interface ChatResponse {
  content: string
  model: string
  provider: string
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export interface AnalyzeRequest {
  hardware_info: {
    cpu_model: string
    gpu_model: string
    gpu_vram_mb: number
    ram_total_gb: number
    disk_type: string
  }
  performance_data: {
    avg_fps?: number
    min_fps?: number
    load_time_seconds?: number
    [key: string]: any
  }
  benchmark_data?: {
    [key: string]: any
  }
  provider?: string
  model?: string
}

export interface AnalyzeResponse {
  bottleneck: string
  score_loss_percent: number
  upgrade_priority: string[]
  estimated_improvement: string
  reasoning: string
  model: string
  provider: string
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// ================================================
// API Functions
// ================================================

/**
 * 获取可用 AI 提供商列表
 */
export function getProviders(): Promise<LLMProvider[]> {
  return axios.get('/llm/providers').then(res => res.data)
}

/**
 * 通用聊天接口
 */
export function chat(request: ChatRequest): Promise<ChatResponse> {
  return axios.post('/llm/chat', request).then(res => res.data)
}

/**
 * 性能分析接口
 */
export function analyzePerformance(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  return axios.post('/llm/analyze', request).then(res => res.data)
}

/**
 * 简单聊天接口
 */
export function simpleChat(message: string, provider?: string): Promise<{
  content: string
  model: string
  provider: string
}> {
  return axios.post('/llm/chat/simple', { message, provider }).then(res => res.data)
}

/**
 * 测试 LLM 连接
 */
export function testLLM(): Promise<{
  providers: LLMProvider[]
  status: Record<string, { status: string; model?: string; error?: string }>
  default_provider: string
}> {
  return axios.get('/llm/test').then(res => res.data)
}

// ================================================
// Helper Functions
// ================================================

/**
 * 分析硬件性能
 */
export function analyzeHardwarePerformance(
  hardwareInfo: AnalyzeRequest['hardware_info'],
  performanceData: AnalyzeRequest['performance_data'],
  benchmarkData?: AnalyzeRequest['benchmark_data']
): Promise<AnalyzeResponse> {
  return analyzePerformance({
    hardware_info: hardwareInfo,
    performance_data: performanceData,
    benchmark_data: benchmarkData
  })
}

/**
 * 获取免费提供商列表
 */
export function getFreeProviders(): Promise<LLMProvider[]> {
  return getProviders().then(providers => 
    providers.filter(p => p.free)
  )
}
