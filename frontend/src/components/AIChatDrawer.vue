<template>
  <div class="ai-chat-drawer">
    <!-- Header with Settings -->
    <div class="drawer-header">
      <div class="header-title">
        <n-icon size="20" color="#10b981"><BotIcon /></n-icon>
        <span>RoleFit AI</span>
      </div>
      <n-button quaternary circle size="small" @click="showSettings = true">
        <template #icon>
          <n-icon><SettingsIcon /></n-icon>
        </template>
      </n-button>
    </div>

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

    <!-- Settings Modal -->
    <n-modal v-model:show="showSettings" preset="card" title="AI 设置" style="width: 400px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="提供商">
          <n-select 
            v-model:value="settings.provider" 
            :options="providerOptions" 
            filterable 
            tag 
            placeholder="选择或输入自定义提供商"
          />
        </n-form-item>
        
        <!-- 自定义提供商配置 -->
        <template v-if="isCustomProvider">
          <n-form-item label="Base URL">
            <n-input v-model:value="settings.baseUrl" placeholder="如: https://api.example.com/v1" />
          </n-form-item>
        </template>

        <n-form-item label="API Key">
          <n-input 
            v-model:value="settings.apiKey" 
            type="password" 
            show-password-on="click" 
            placeholder="留空则使用系统默认"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input v-model:value="settings.model" placeholder="如: Qwen/Qwen2.5-7B-Instruct" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px;">
          <n-button @click="showSettings = false">取消</n-button>
          <n-button type="primary" @click="saveSettings">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, reactive, computed } from 'vue'
import { NButton, NIcon, NInput, NModal, NForm, NFormItem, NSelect, useMessage } from 'naive-ui'
import { 
  Send as SendIcon,
  PersonCircle as UserIcon,
  HardwareChip as BotIcon,
  SettingsOutline as SettingsIcon
} from '@vicons/ionicons5'
import { marked } from 'marked'

// API
import { agentChat } from '@/api/ai'

const message = useMessage()
const inputText = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const showSettings = ref(false)

// Settings
const settings = reactive({
  provider: localStorage.getItem('ai_provider') || 'siliconflow',
  baseUrl: localStorage.getItem('ai_base_url') || '',
  apiKey: localStorage.getItem('ai_api_key') || '',
  model: localStorage.getItem('ai_model') || ''
})

const providerOptions = [
  { label: '硅基流动 (SiliconFlow)', value: 'siliconflow' },
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '通义千问 (Qwen)', value: 'qwen' },
  { label: '智谱 AI', value: 'zhipu' },
  { label: '自定义 (Custom)', value: 'custom' }
]

const isCustomProvider = computed(() => {
  return settings.provider === 'custom' || !providerOptions.find(p => p.value === settings.provider)
})

function saveSettings() {
  localStorage.setItem('ai_provider', settings.provider)
  localStorage.setItem('ai_base_url', settings.baseUrl)
  localStorage.setItem('ai_api_key', settings.apiKey)
  localStorage.setItem('ai_model', settings.model)
  showSettings.value = false
  message.success('设置已保存')
  
  // Add system message
  addMessage(`配置已更新！\n- 提供商: ${settings.provider}\n- 模型: ${settings.model || '默认'}`)
}

// 初始化消息
const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是 RoleFit Pro AI 助手 🤖\n\n我已经升级为智能 Agent 模式。你可以直接用自然语言让我帮你：\n\n- "帮我看看现在有哪些在线的设备"\n- "查询最近失败的测试任务"\n- "有没有 RTX 4090 的机器？"\n- "查看 PC-001 的性能状态"\n\n请试着告诉我你想做什么！',
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
    // 构造历史消息上下文 (排除 loading 状态的消息)
    // 只保留最近 10 条，避免 token 过长
    const history = messages.value
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map(m => ({
        role: m.role,
        content: m.content
      }))
      
    // 调用后端 Agent (带上配置)
    const res = await agentChat(
      text, 
      history, 
      settings.provider, 
      settings.apiKey, 
      settings.model,
      settings.baseUrl // 新增参数
    )
    
    if (res && res.content) {
      addMessage(res.content)
    } else {
      addMessage('🤔 AI 似乎没有返回内容，请稍后再试。')
    }

  } catch (error) {
    console.error('Error:', error)
    addMessage('❌ 处理出错: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-chat-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  background: #fff;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
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
