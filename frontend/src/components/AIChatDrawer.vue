<template>
  <div class="ai-chat-drawer">
    <!-- 聊天消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="message-avatar">
          <n-icon v-if="msg.role === 'assistant'" size="20">
            <BotIcon />
          </n-icon>
          <n-icon v-else size="20">
            <UserIcon />
          </n-icon>
        </div>
        <div class="message-content">
          <!-- 使用 marked 渲染 Markdown -->
          <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="message assistant">
        <div class="message-avatar">
          <n-icon size="20"><BotIcon /></n-icon>
        </div>
        <div class="message-content">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入框 -->
    <div class="chat-input">
      <n-input
        v-model:value="inputText"
        type="textarea"
        placeholder="输入你的问题..."
        :autosize="{ minRows: 1, maxRows: 3 }"
        class="chat-input-field"
        @keydown.enter.exact.prevent="sendMessage"
      />
      <n-button 
        type="primary" 
        :loading="loading" 
        @click="sendMessage" 
        class="send-button"
        :disabled="!inputText.trim()"
      >
        <template #icon>
          <n-icon><SendIcon /></n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { NButton, NIcon, NInput } from 'naive-ui'
import { 
  Send as SendIcon,
  PersonCircle as UserIcon,
  HardwareChip as BotIcon
} from '@vicons/ionicons5'
import { marked } from 'marked'

// API
import { 
  getDevices, 
  getDeviceStatus,
  getPerformanceMetrics,
  getTasks
} from '@/api/devices'
import { aiAnalyze } from '@/api/ai'
import { softwareApi } from '@/api/software'
import { scriptApi } from '@/api/scripts'
import { resultApi } from '@/api/results'
import { statsApi } from '@/api/stats'

const inputText = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

// 初始化消息
const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是 RoleFit Pro AI 助手 🤖\n\n我可以帮你：\n- 查询设备列表和状态\n- 查看性能监控数据\n- 查询测试结果和统计\n\n直接问我问题吧！',
    timestamp: new Date().toISOString()
  }
])

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

function renderMarkdown(content) {
  if (!content) return ''
  return marked.parse(content)
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function addMessage(content, role = 'assistant') {
  const newMsg = {
    role,
    content,
    timestamp: new Date().toISOString()
  }
  messages.value.push(newMsg)
  // 强制更新
  messages.value = [...messages.value]
  nextTick(() => scrollToBottom())
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  
  // 添加用户消息
  addMessage(text, 'user')
  inputText.value = ''
  loading.value = true
  
  try {
    // 处理意图
    const handled = await handleIntent(text)
    if (!handled) {
      // 使用 AI 分析
      await aiAnalyzeMessage(text)
    }
  } catch (error) {
    console.error('Error:', error)
    addMessage('❌ 处理出错: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function handleIntent(text) {
  const lower = text.toLowerCase()
  
  // 关于AI模型
  if (lower.includes('什么') && (lower.includes('模型') || lower.includes('大模型'))) {
    addMessage('我使用的是 **NVIDIA Llama 3.1** 大模型 (meta/llama-3.1-8b-instruct)。')
    return true
  }
  
  // 设备列表 - 直接API查询 + Markdown表格
  if (lower.includes('设备') && (lower.includes('列表') || lower.includes('所有') || lower.includes('列') || lower.includes('显示'))) {
    await listDevicesMarkdown()
    return true
  }
  
  // 设备状态
  if (lower.includes('设备') && (lower.includes('状态') || lower.includes('在线'))) {
    await queryDeviceStatus()
    return true
  }
  
  // 性能
  if (lower.includes('性能') || lower.includes('监控')) {
    await viewPerformance()
    return true
  }
  
  // 任务
  if ((lower.includes('任务') || lower.includes('测试')) && (lower.includes('列表') || lower.includes('查看'))) {
    await listTasks()
    return true
  }
  
  // 软件
  if (lower.includes('软件') && (lower.includes('列表') || lower.includes('所有'))) {
    await listSoftware()
    return true
  }
  
  // 脚本
  if (lower.includes('脚本')) {
    await listScripts()
    return true
  }
  
  // 结果
  if (lower.includes('结果') || lower.includes('分数')) {
    await listResults()
    return true
  }
  
  // 统计
  if (lower.includes('统计') || lower.includes('仪表盘') || lower.includes('概览')) {
    await viewStats()
    return true
  }
  
  // 创建任务
  if (lower.includes('创建') && lower.includes('任务')) {
    addMessage('好的，请告诉我：\n1. 要测试哪个设备？\n2. 需要做什么测试？')
    return true
  }
  
  // 帮助
  if (lower.includes('帮助') || lower === '?') {
    showHelp()
    return true
  }
  
  return false
}

// 设备列表 - Markdown表格格式
async function listDevicesMarkdown() {
  try {
    addMessage('🔍 正在查询设备列表...')
    
    const res = await getDevices({ page_size: 20 })
    const devices = res.items || res || []
    
    if (!devices.length) {
      addMessage('暂未发现任何设备。')
      return
    }
    
    // 生成 Markdown 表格
    let md = '| 设备名称 | 状态 | CPU | GPU |\n'
    md += '| --- | --- | --- | --- |\n'
    
    devices.forEach(d => {
      const status = d.status === 'online' ? '🟢 在线' : '🔴 离线'
      const cpu = d.cpu_model ? d.cpu_model.substring(0, 20) : '未知'
      const gpu = d.gpu_model ? d.gpu_model.substring(0, 20) : '未知'
      md += `| ${d.device_name} | ${status} | ${cpu} | ${gpu} |\n`
    })
    
    addMessage(`📊 **设备列表** (共 ${devices.length} 台)\n\n${md}`)
  } catch (e) {
    console.error('List devices error:', e)
    addMessage('❌ 获取设备列表失败: ' + e.message)
  }
}

async function queryDeviceStatus() {
  try {
    addMessage('🔍 正在查询设备状态...')
    
    const res = await getDevices({ page_size: 5 })
    const devices = res.items || res || []
    
    if (!devices.length) {
      addMessage('暂未发现任何设备。')
      return
    }
    
    let md = '| 设备 | 状态 | CPU | GPU | 内存 |\n'
    md += '| --- | --- | --- | --- | --- |\n'
    
    for (const device of devices) {
      try {
        const status = await getDeviceStatus(device.id)
        const isOnline = status?.latest_metric ? '🟢' : '🔴'
        const cpu = status?.latest_metric?.cpu_percent?.toFixed(1) + '%' || '-'
        const gpu = status?.latest_metric?.gpu_percent?.toFixed(1) + '%' || '-'
        const mem = status?.latest_metric?.memory_percent?.toFixed(1) + '%' || '-'
        md += `| ${device.device_name} | ${isOnline} | ${cpu} | ${gpu} | ${mem} |\n`
      } catch {
        md += `| ${device.device_name} | ❌ | - | - | - |\n`
      }
    }
    
    addMessage(`📱 **设备状态**\n\n${md}`)
  } catch (e) {
    console.error('Status error:', e)
    addMessage('❌ 获取设备状态失败: ' + e.message)
  }
}

async function viewPerformance() {
  try {
    addMessage('🔍 正在查询性能数据...')
    
    const res = await getDevices({ page_size: 3 })
    const devices = res.items || res || []
    
    if (!devices.length) {
      addMessage('暂未发现任何设备。')
      return
    }
    
    let md = '| 设备 | CPU | GPU | 内存 |\n'
    md += '| --- | --- | --- | --- |\n'
    
    for (const device of devices) {
      try {
        const metrics = await getPerformanceMetrics(device.id, { limit: 1 })
        const data = metrics.items?.[0] || metrics?.[0]
        
        if (data) {
          const cpu = data.cpu_percent?.toFixed(1) + '%' || '-'
          const gpu = data.gpu_percent?.toFixed(1) + '%' || '-'
          const mem = data.memory_percent?.toFixed(1) + '%' || '-'
          md += `| ${device.device_name} | ${cpu} | ${gpu} | ${mem} |\n`
        } else {
          md += `| ${device.device_name} | 无数据 | 无数据 | 无数据 |\n`
        }
      } catch {
        md += `| ${device.device_name} | 查询失败 | 查询失败 | 查询失败 |\n`
      }
    }
    
    addMessage(`📈 **实时性能**\n\n${md}`)
  } catch (e) {
    console.error('Performance error:', e)
    addMessage('❌ 获取性能数据失败: ' + e.message)
  }
}

async function listTasks() {
  try {
    const res = await getTasks({ page_size: 10 })
    const tasks = res.items || res || []
    
    if (!tasks.length) {
      addMessage('暂无测试任务。')
      return
    }
    
    let md = '| 任务名 | 类型 | 状态 | 创建时间 |\n'
    md += '| --- | --- | --- | --- |\n'
    
    tasks.forEach(t => {
      const status = t.task_status === 'completed' ? '✅' : t.task_status === 'running' ? '🔄' : '⏳'
      const time = new Date(t.created_at).toLocaleDateString('zh-CN')
      md += `| ${t.task_name} | ${t.task_type || '-'} | ${status} | ${time} |\n`
    })
    
    addMessage(`📋 **测试任务** (${tasks.length}个)\n\n${md}`)
  } catch (e) {
    addMessage('❌ 获取任务列表失败: ' + e.message)
  }
}

async function listSoftware() {
  try {
    const res = await softwareApi.list({ page_size: 10 })
    const software = res.items || res || []
    
    if (!software.length) {
      addMessage('暂未添加任何软件。')
      return
    }
    
    let md = '| 软件名 | 类别 | 版本 | 状态 |\n'
    md += '| --- | --- | --- | --- |\n'
    
    software.forEach(s => {
      const status = s.is_active ? '✅' : '❌'
      md += `| ${s.software_name} | ${s.category || '-'} | ${s.version || '-'} | ${status} |\n`
    })
    
    addMessage(`💻 **软件列表** (${software.length}个)\n\n${md}`)
  } catch (e) {
    addMessage('❌ 获取软件列表失败: ' + e.message)
  }
}

async function listScripts() {
  try {
    const res = await scriptApi.list({ page_size: 10 })
    const scripts = res.items || res || []
    
    if (!scripts.length) {
      addMessage('暂未添加任何测试脚本。')
      return
    }
    
    let md = '| 脚本名 | 类型 | 预计时长 |\n'
    md += '| --- | --- | --- |\n'
    
    scripts.forEach(s => {
      md += `| ${s.script_name} | ${s.script_type || '标准'} | ${s.expected_duration}分钟 |\n`
    })
    
    addMessage(`📜 **测试脚本** (${scripts.length}个)\n\n${md}`)
  } catch (e) {
    addMessage('❌ 获取脚本列表失败: ' + e.message)
  }
}

async function listResults() {
  try {
    const res = await resultApi.list({ page_size: 10 })
    const results = res.items || res || []
    
    if (!results.length) {
      addMessage('暂无测试结果。')
      return
    }
    
    let md = '| 设备 | 测试类型 | 状态 | 得分 | 日期 |\n'
    md += '| --- | --- | --- | --- | --- |\n'
    
    results.forEach(r => {
      const status = r.test_status === 'passed' ? '✅' : r.test_status === 'failed' ? '❌' : '⏳'
      const score = r.overall_score || '-'
      const date = new Date(r.created_at).toLocaleDateString('zh-CN')
      md += `| ${r.device_id} | ${r.test_type || '-'} | ${status} | ${score} | ${date} |\n`
    })
    
    addMessage(`📊 **测试结果** (${results.length}条)\n\n${md}`)
  } catch (e) {
    addMessage('❌ 获取测试结果失败: ' + e.message)
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
    
    const md = `
| 指标 | 数值 |
| --- | --- |
| 🖥️ 总设备 | ${stats.total_devices} |
| 🟢 在线 | ${stats.online_devices} (${onlineRate}%) |
| 📋 总任务 | ${stats.total_tasks} |
| ✅ 已完成 | ${stats.completed_tasks} |
| 🧪 总测试 | ${stats.total_tests} |
| ✅ 通过 | ${stats.passed_tests} (${passRate}%) |
| 📊 平均分 | ${stats.average_score?.toFixed(1) || 0} |
`
    
    addMessage(`📈 **系统概览**\n\n${md}`)
  } catch (e) {
    addMessage('❌ 获取统计数据失败: ' + e.message)
  }
}

function showHelp() {
  addMessage(`🤖 **可用命令**：

| 功能 | 命令示例 |
| --- | --- |
| 设备列表 | "查看设备列表" |
| 设备状态 | "查看设备状态" |
| 性能监控 | "查看性能" |
| 任务列表 | "查看任务" |
| 软件列表 | "查看软件" |
| 测试结果 | "查看测试结果" |
| 系统统计 | "查看统计" |

💬 也可以直接问我任何问题！`)
}

async function aiAnalyzeMessage(text) {
  try {
    addMessage('🤔 AI 正在思考...')
    
    const result = await aiAnalyze({
      query: text,
      analysis_type: 'general'
    })
    
    // 移除"正在思考"消息
    messages.value.pop()
    
    if (result?.summary) {
      addMessage(result.summary)
    } else if (result?.detail) {
      addMessage('❌ AI 返回错误: ' + result.detail)
    } else {
      addMessage('抱歉，我暂时无法回答。你可以尝试：\n- 查看设备列表\n- 查看设备状态')
    }
  } catch (e) {
    // 移除"正在思考"消息
    if (messages.value.length > 0 && messages.value[messages.value.length - 1].content.includes('思考')) {
      messages.value.pop()
    }
    console.error('AI error:', e)
    addMessage('❌ AI 分析失败: ' + e.message)
  }
}
</script>

<style scoped>
.ai-chat-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fafafa;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 95%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
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
  border-radius: 14px;
  padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
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
  font-size: 13px;
  word-break: break-word;
}

/* Markdown 表格样式 */
.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 6px 10px;
  text-align: left;
}

.message-text :deep(th) {
  background: #f3f4f6;
  font-weight: 600;
}

.message-text :deep(tr:nth-child(even)) {
  background: #f9fafb;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: #1f2937;
}

.message-text :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.message-time {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 6px;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: #fff;
}

.chat-input-field {
  flex: 1;
}

.send-button {
  flex-shrink: 0;
}

.send-button:disabled {
  opacity: 0.5;
}
</style>
