/**
 * LLM Config API - 大模型配置接口
 */

import axios from './index'

// ================================================
// Types
// ================================================

export interface LLMConfig {
  id: string
  provider: string
  api_key?: string
  model?: string
  is_active: boolean
  status?: 'ok' | 'error' | 'untested'
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  model?: string
  provider?: string
  created_at: string
}

export interface TestResult {
  status: 'ok' | 'error'
  model?: string
  response?: string
  provider?: string
  error?: string
}

// ================================================
// API Functions
// ================================================

/**
 * 获取 LLM 配置
 */
export function getLLMConfig(): Promise<LLMConfig> {
  return axios.get('/llm-config/config').then(res => res.data)
}

/**
 * 保存 LLM 配置
 */
export function saveLLMConfig(config: {
  provider?: string
  api_key?: string
  model?: string
  is_active?: boolean
}): Promise<LLMConfig> {
  return axios.post('/llm-config/config', config).then(res => res.data)
}

/**
 * 测试提供商连接
 */
export function testProvider(
  provider: string,
  apiKey?: string,
  model?: string
): Promise<TestResult> {
  return axios.post('/llm-config/test', null, {
    params: { provider, api_key: apiKey, model }
  }).then(res => res.data)
}

/**
 * 获取对话历史
 */
export function getChatHistory(sessionId: string, limit?: number): Promise<ChatMessage[]> {
  return axios.get(`/llm-config/chat/${sessionId}`, {
    params: { limit }
  }).then(res => res.data)
}

/**
 * 发送对话消息
 */
export function sendChatMessage(
  sessionId: string,
  message: {
    role: string
    content: string
    model?: string
    provider?: string
  }
): Promise<ChatMessage> {
  return axios.post(`/llm-config/chat/${sessionId}`, message).then(res => res.data)
}

/**
 * 清除对话历史
 */
export function clearChatHistory(sessionId: string): Promise<{ status: string }> {
  return axios.delete(`/llm-config/chat/${sessionId}`).then(res => res.data)
}
