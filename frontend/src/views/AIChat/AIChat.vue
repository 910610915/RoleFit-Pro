<template>
  <div class="ai-chat-container">
    <!-- 聊天消息列表 -->
    <div class="chat-messages" v-auto-animate>
      <div
        v-for="(msg, index) in messages"
        :key="msg.timestamp + '-' + msg.role"
        :class="['message', msg.role]"
      >
        <div class="message-avatar">
          <n-icon v-if="msg.role === 'assistant'" size="22">
            <BotIcon />
          </n-icon>
          <n-icon v-else size="22">
            <UserIcon />
          </n-icon>
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="message assistant">
        <div class="message-avatar">
          <n-icon size="22"><BotIcon /></n-icon>
        </div>
        <div class="message-content">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快捷操作 -->
    <div class="quick-actions" v-auto-animate>
      <n-tag 
        v-for="action in quickActions" 
        :key="action.text"
        size="small" 
        :bordered="false"
        type="info"
        class="quick-tag"
        @click="executeQuickAction(action)"
      >
        {{ action.text }}
      </n-tag>
    </div>
    
    <!-- 输入框 -->
    <div class="chat-input">
      <n-input
        v-model:value="inputText"
        type="textarea"
        placeholder="输入你的问题..."
        :autosize="{ minRows: 1, maxRows: 4 }"
        class="chat-input-field"
        @keydown.enter.exact.prevent="sendMessage"
      />
      <n-button type="primary" :loading="loading" @click="sendMessage" class="send-button">
        <template #icon>
          <n-icon><SendIcon /></n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch, triggerRef } from 'vue'
import { NButton, NIcon, NTag, NInput } from 'naive-ui'
import { useAutoAnimate } from '@formkit/auto-animate/vue'
import { 
  Send as SendIcon,
  PersonCircle as UserIcon,
  HardwareChip as BotIcon
} from '@vicons/ionicons5'

// API
import { 
  getDevices, 
  getDeviceById,
  getDeviceStatus,
  getPerformanceMetrics,
  getBenchmarks,
  getTasks,
  createTask
} from '@/api/devices'
import { aiAnalyze } from '@/api/ai'
import { softwareApi } from '@/api/software'
import { scriptApi } from '@/api/scripts'
import { resultApi } from '@/api/results'
import { statsApi } from '@/api/stats'

// 使用 auto-animate - 只需要直接调用，不需要额外处理
useAutoAnimate()

const inputText = ref('')
const loading = ref(false)
const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是 RoleFit Pro AI 助手 🤖\n\n我可以帮你：\n• 查询设备性能和状态\n• 创建测试任务\n• 分析性能瓶颈\n• 查看软件和脚本列表\n• 查询测试结果和统计\n• 获取升级建议\n\n请告诉我你需要什么帮助？',
    timestamp: new Date().toISOString()
  }
])

const quickActions = [
  { text: '查看所有设备', intent: 'list_devices' },
  { text: '查看性能监控', intent: 'view_performance' },
  { text: '创建测试任务', intent: 'create_task' },
  { text: '设备状态查询', intent: 'query_status' },
  { text: '查看软件列表', intent: 'list_software' },
  { text: '查看测试结果', intent: 'list_results' },
  { text: '系统统计', intent: 'view_stats' },
]

onMounted(() => {
  scrollToBottom()
})

watch(messages, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })

function scrollToBottom() {
  const container = document.querySelector('.chat-messages')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatMessage(content) {
  if (!content) return ''
  return content.replace(/\n/g, '<br>').replace(/• /g, '• ')
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: new Date().toISOString()
  })
  triggerRef(messages) // Force reactivity
  
  inputText.value = ''
  loading.value = true
  
  try {
    const intent = recognizeIntent(text)
    await processIntent(intent)
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，处理你的请求时出现错误。请稍后重试。',
      timestamp: new Date().toISOString()
    })
    triggerRef(messages)
  } finally {
    loading.value = false
  }
}

function recognizeIntent(text) {
  const lowerText = text.toLowerCase()
  
  // 软件/程序相关
  if (lowerText.includes('软件') || lowerText.includes('程序') || lowerText.includes('安装')) {
    if (lowerText.includes('列表') || lowerText.includes('所有') || lowerText.includes('查看') || lowerText.includes('显示')) {
      return { type: 'list_software' }
    }
    if (lowerText.includes('安装') || lowerText.includes('检测')) {
      return { type: 'check_software' }
    }
  }
  
  // 脚本相关
  if (lowerText.includes('脚本') || lowerText.includes('测试脚本')) {
    if (lowerText.includes('列表') || lowerText.includes('所有') || lowerText.includes('查看') || lowerText.includes('显示') || lowerText.includes('列')) {
      return { type: 'list_scripts' }
    }
  }
  
  // 结果/测试结果
  if (lowerText.includes('结果') || lowerText.includes('测试成绩') || lowerText.includes('分数')) {
    if (lowerText.includes('列表') || lowerText.includes('所有') || lowerText.includes('查看') || lowerText.includes('显示') || lowerText.includes('列')) {
      return { type: 'list_results' }
    }
    if (lowerText.includes('对比') || lowerText.includes('比较')) {
      return { type: 'compare_results' }
    }
  }
  
  // 统计/仪表盘
  if (lowerText.includes('统计') || lowerText.includes('仪表盘') || lowerText.includes('概览') || lowerText.includes('总览')) {
    return { type: 'view_stats' }
  }
  
  // 设备相关 - 修复：增加更多匹配模式
  if (lowerText.includes('设备') || lowerText.includes('电脑') || lowerText.includes('机器')) {
    if (lowerText.includes('列表') || lowerText.includes('所有') || lowerText.includes('列') || lowerText.includes('显示') || lowerText.includes('查看')) {
      return { type: 'list_devices' }
    }
    if (lowerText.includes('状态') || lowerText.includes('在线')) {
      return { type: 'query_status' }
    }
    if (lowerText.includes('性能') || lowerText.includes('监控')) {
      return { type: 'view_performance' }
    }
  }
  
  // 任务相关
  if (lowerText.includes('任务') || lowerText.includes('测试')) {
    if (lowerText.includes('创建') || lowerText.includes('新建')) {
      return { type: 'create_task' }
    }
    if (lowerText.includes('列表') || lowerText.includes('查看') || lowerText.includes('所有')) {
      return { type: 'list_tasks' }
    }
  }
  
  // 分析相关
  if (lowerText.includes('分析') || lowerText.includes('瓶颈') || lowerText.includes('建议')) {
    return { type: 'analyze' }
  }
  
  if (lowerText.includes('帮助') || lowerText === '?') {
    return { type: 'help' }
  }
  
  return { type: 'ai_analyze', text }
}

async function processIntent(intent) {
  switch (intent.type) {
    case 'list_devices': await listDevices(); break
    case 'query_status': await queryDeviceStatus(intent.deviceId); break
    case 'view_performance': await viewPerformance(intent.deviceId); break
    case 'create_task': await createTestTask(); break
    case 'list_tasks': await listTasks(); break
    case 'analyze': await analyzePerformance(intent.deviceId); break
    case 'ai_analyze': await aiAnalyzeMessage(intent.text); break
    case 'help': await showHelp(); break
    // 新增API集成
    case 'list_software': await listSoftware(); break
    case 'list_scripts': await listScripts(); break
    case 'list_results': await listResults(); break
    case 'view_stats': await viewStats(); break
    default: await aiAnalyzeMessage(intent.text || '我不知道怎么处理这个请求')
  }
}

async function listDevices() {
  try {
    const res = await getDevices({ page_size: 10 })
    const devices = res.items || []
    
    if (devices.length === 0) {
      addMessage('暂未发现任何设备。')
      return
    }
    
    let message = '📊 设备列表：\n\n'
    devices.forEach(d => {
      const status = d.status === 'online' ? '🟢 在线' : '🔴 离线'
      message += `• ${d.device_name} - ${status}\n`
      message += `  CPU: ${d.cpu_model || '未知'}\n`
      message += `  GPU: ${d.gpu_model || '未知'}\n\n`
    })
    
    message += '你可以问我具体设备的详细信息，例如："查看 DEV-001 的性能"'
    addMessage(message)
  } catch (e) {
    addMessage('获取设备列表失败：' + e.message)
  }
}

async function queryDeviceStatus(deviceId) {
  try {
    if (!deviceId) {
      const res = await getDevices({ page_size: 5 })
      if (res.items.length === 0) {
        addMessage('暂未发现任何设备。')
        return
      }
      deviceId = res.items[0].id
    }
    
    const status = await getDeviceStatus(deviceId)
    const statusText = status.latest_metric ? '🟢 在线' : '🔴 离线'
    
    let message = `📱 设备状态：${statusText}\n\n`
    
    if (status.latest_metric) {
      message += `CPU: ${status.latest_metric.cpu_percent?.toFixed(1)}%\n`
      message += `GPU: ${status.latest_metric.gpu_percent?.toFixed(1)}%\n`
      message += `内存: ${status.latest_metric.memory_percent?.toFixed(1)}%\n`
    }
    
    if (status.pending_alerts_count > 0) {
      message += `\n⚠️ 待处理告警: ${status.pending_alerts_count} 个`
    }
    
    addMessage(message)
  } catch (e) {
    addMessage('获取设备状态失败：' + e.message)
  }
}

async function viewPerformance(deviceId) {
  try {
    if (!deviceId) {
      const res = await getDevices({ page_size: 5 })
      if (res.items.length === 0) {
        addMessage('暂未发现任何设备。')
        return
      }
      deviceId = res.items[0].id
    }
    
    const metrics = await getPerformanceMetrics(deviceId, { limit: 10 })
    
    if (!metrics.items || metrics.items.length === 0) {
      addMessage('该设备暂无性能数据。')
      return
    }
    
    const latest = metrics.items[0]
    const message = `📈 设备性能 (最近):\n\n`
      + `CPU: ${latest.cpu_percent?.toFixed(1) || 0}%\n`
      + `GPU: ${latest.gpu_percent?.toFixed(1) || 0}%\n`
      + `内存: ${latest.memory_percent?.toFixed(1) || 0}%\n`
      + `磁盘IO: ${latest.disk_read_mbps?.toFixed(1) || 0} MB/s`
    
    addMessage(message)
  } catch (e) {
    addMessage('获取性能数据失败：' + e.message)
  }
}

async function createTestTask() {
  addMessage('好的，我来帮你创建测试任务。请告诉我：\n\n1. 你想测试哪个设备？\n2. 需要做什么测试？（如：Blender渲染、Maya动画、Unreal编译等）')
}

async function listTasks() {
  try {
    const res = await getTasks({ page_size: 5 })
    const tasks = res.items || []
    
    if (tasks.length === 0) {
      addMessage('暂无测试任务。')
      return
    }
    
    let message = '📋 测试任务：\n\n'
    tasks.forEach(t => {
      const status = t.task_status === 'completed' ? '✅' : t.task_status === 'running' ? '🔄' : '⏳'
      message += `${status} ${t.task_name}\n`
      message += `   状态: ${t.task_status}\n\n`
    })
    
    addMessage(message)
  } catch (e) {
    addMessage('获取任务列表失败：' + e.message)
  }
}

async function listSoftware() {
  try {
    const res = await softwareApi.list({ page_size: 10 })
    const software = res.items || []
    
    if (software.length === 0) {
      addMessage('暂未添加任何软件。')
      return
    }
    
    let message = '💻 软件列表：\n\n'
    software.forEach(s => {
      const category = s.category || '未分类'
      message += `• ${s.software_name}\n`
      message += `  类别: ${category}\n`
      message += `  版本: ${s.version || '未知'}\n`
      message += `  状态: ${s.is_active ? '✅ 启用' : '❌ 禁用'}\n\n`
    })
    
    message += '你可以问我"检测某设备的软件"来检查软件安装情况。'
    addMessage(message)
  } catch (e) {
    addMessage('获取软件列表失败：' + e.message)
  }
}

async function listScripts() {
  try {
    const res = await scriptApi.list({ page_size: 10 })
    const scripts = res.items || []
    
    if (scripts.length === 0) {
      addMessage('暂未添加任何测试脚本。')
      return
    }
    
    let message = '📜 测试脚本：\n\n'
    scripts.forEach(s => {
      const type = s.script_type || '标准测试'
      message += `• ${s.script_name}\n`
      message += `  类型: ${type}\n`
      message += `  预计时长: ${s.expected_duration}分钟\n\n`
    })
    
    message += '你可以创建任务来执行这些脚本。'
    addMessage(message)
  } catch (e) {
    addMessage('获取脚本列表失败：' + e.message)
  }
}

async function listResults() {
  try {
    const res = await resultApi.list({ page_size: 5 })
    const results = res.items || []
    
    if (results.length === 0) {
      addMessage('暂无测试结果。')
      return
    }
    
    let message = '📊 测试结果：\n\n'
    results.forEach(r => {
      const status = r.test_status === 'passed' ? '✅ 通过' : r.test_status === 'failed' ? '❌ 失败' : '⏳ 进行中'
      const score = r.overall_score ? `得分: ${r.overall_score}` : ''
      message += `• 设备: ${r.device_id}\n`
      message += `  状态: ${status}\n`
      if (score) message += `  ${score}\n`
      message += `  时间: ${new Date(r.created_at).toLocaleString('zh-CN')}\n\n`
    })
    
    message += '你可以问我"对比设备"来比较不同设备的性能。'
    addMessage(message)
  } catch (e) {
    addMessage('获取测试结果失败：' + e.message)
  }
}

async function viewStats() {
  try {
    const stats = await statsApi.getDashboard()
    
    const onlineRate = stats.total_devices > 0 
      ? ((stats.online_devices / stats.total_devices) * 100).toFixed(1) 
      : 0
    const passRate = stats.total_tests > 0 
      ? ((stats.passed_tests / stats.total_tests) * 100).toFixed(1) 
      : 0
    
    let message = `📈 系统概览\n\n`
    message += `🖥️ 设备统计:\n`
    message += `  • 总设备: ${stats.total_devices}\n`
    message += `  • 在线: ${stats.online_devices} (${onlineRate}%)\n`
    message += `  • 离线: ${stats.offline_devices}\n`
    message += `  • 测试中: ${stats.testing_devices}\n\n`
    
    message += `📋 任务统计:\n`
    message += `  • 总任务: ${stats.total_tasks}\n`
    message += `  • 待处理: ${stats.pending_tasks}\n`
    message += `  • 进行中: ${stats.running_tasks}\n`
    message += `  • 已完成: ${stats.completed_tasks}\n\n`
    
    message += `🧪 测试统计:\n`
    message += `  • 总测试: ${stats.total_tests}\n`
    message += `  • 通过: ${stats.passed_tests} (${passRate}%)\n`
    message += `  • 失败: ${stats.failed_tests}\n`
    message += `  • 平均分: ${stats.average_score?.toFixed(1) || 0}\n`
    
    addMessage(message)
  } catch (e) {
    addMessage('获取统计数据失败：' + e.message)
  }
}

async function analyzePerformance(deviceId) {
  try {
    addMessage('🔍 正在分析设备性能，请稍候...')
    
    const result = await aiAnalyze({
      device_id: deviceId,
      analysis_type: 'performance_trend'
    })
    
    if (result.summary) {
      addMessage(`📊 AI 分析报告：\n\n${result.summary}`)
      if (result.recommendations) {
        addMessage(`💡 建议：\n\n${result.recommendations}`)
      }
    } else {
      addMessage('分析完成，但暂无详细数据。')
    }
  } catch (e) {
    addMessage('AI 分析失败：' + e.message)
  }
}

async function aiAnalyzeMessage(text) {
  try {
    addMessage('🤔 正在思考...')
    triggerRef(messages)
    
    const result = await aiAnalyze({
      query: text,
      analysis_type: 'general'
    })
    
    if (result.summary) {
      addMessage(result.summary)
    } else {
      addMessage('抱歉，我暂时无法回答这个问题。你可以尝试：\n• 查看设备列表\n• 查询设备状态\n• 创建测试任务')
    }
    triggerRef(messages)
  } catch (e) {
    addMessage('AI 分析暂时不可用。你可以尝试直接查询设备信息。')
    triggerRef(messages)
  }
}

async function showHelp() {
  addMessage(`🤖 可用命令：

📱 设备管理
• "查看所有设备" - 列出设备
• "查看设备状态" - 查询在线状态
• "查看性能" - 性能监控数据

📋 任务管理
• "创建测试任务" - 新建任务
• "查看任务" - 任务列表

💻 软件管理
• "查看软件列表" - 列出所有软件
• "软件检测" - 检测软件安装情况

📜 脚本管理
• "查看脚本列表" - 列出所有测试脚本

📊 结果与统计
• "查看测试结果" - 最近的测试成绩
• "查看统计" / "查看仪表盘" - 系统概览

📊 分析功能
• "分析性能" - AI 性能分析
• "瓶颈分析" - 查找性能瓶颈
• "升级建议" - 获取硬件升级建议

💬 直接输入你想问的问题，我会尽力帮你解答！`)
}

function addMessage(content) {
  messages.value.push({
    role: 'assistant',
    content,
    timestamp: new Date().toISOString()
  })
  // Force trigger reactivity to ensure UI updates
  triggerRef(messages)
}

async function executeQuickAction(action) {
  await processIntent({ type: action.intent })
}
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: #fff;
}

.message-content {
  background: #fff;
  border-radius: 18px;
  padding: 14px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
}

.message.assistant .message-content {
  border-top-left-radius: 4px;
}

.message.user .message-content {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border-top-right-radius: 4px;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 14px;
}

.message-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 6px;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.loading-dots {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.loading-dots span {
  width: 10px;
  height: 10px;
  background: #10b981;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% { 
    transform: scale(1);
    opacity: 1;
  }
}

.quick-actions {
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.quick-tag:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.chat-input-field {
  flex: 1;
}

.chat-input-field :deep(.n-input__textarea-el) {
  border-radius: 12px;
}

.send-button {
  height: auto;
  border-radius: 12px;
  padding: 8px 16px;
}

.send-button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}
</style>
