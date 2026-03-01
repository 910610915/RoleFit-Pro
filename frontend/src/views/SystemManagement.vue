<template>
  <div class="system-management">
    <div class="page-header">
      <h1>系统管理</h1>
      <p>配置功能卡片和数据库管理</p>
    </div>
    
    <n-tabs type="line" animated>
      <!-- Feature Cards Tab -->
      <n-tab-pane name="cards" tab="功能卡片管理">
        <n-card>
          <div class="toolbar">
            <n-button type="primary" @click="showAddModal = true">
              新增卡片
            </n-button>
          </div>
          
          <n-data-table
            :columns="columns"
            :data="cards"
            :row-key="(row: FeatureCard) => row.id"
            :bordered="false"
          />
        </n-card>
        
        <!-- Add/Edit Modal -->
        <n-modal v-model:show="showAddModal" preset="card" :style="{ width: '500px' }" :title="editingCard ? '编辑卡片' : '新增卡片'">
          <n-form ref="formRef" :model="formData" :rules="rules">
            <n-form-item label="卡片标识" path="card_key" v-if="!editingCard">
              <n-input v-model:value="formData.card_key" placeholder="如: my-custom-feature" />
            </n-form-item>
            <n-form-item label="标题" path="title">
              <n-input v-model:value="formData.title" placeholder="卡片显示标题" />
            </n-form-item>
            <n-form-item label="描述" path="description">
              <n-input v-model:value="formData.description" type="textarea" placeholder="卡片描述文字" />
            </n-form-item>
            <n-form-item label="图标" path="icon">
              <n-select v-model:value="formData.icon" :options="iconOptions" placeholder="选择图标" />
            </n-form-item>
            <n-form-item label="路由" path="route">
              <n-input v-model:value="formData.route" placeholder="如: /my-page" />
            </n-form-item>
            <n-form-item label="显示" path="is_visible">
              <n-switch v-model:value="formData.is_visible" />
            </n-form-item>
          </n-form>
          
          <template #footer>
            <n-button @click="showAddModal = false">取消</n-button>
            <n-button type="primary" @click="saveCard" :loading="saving">保存</n-button>
          </template>
        </n-modal>
      </n-tab-pane>
      
      <!-- Database Tab -->
      <n-tab-pane name="database" tab="数据库管理">
        <n-card title="数据库导出">
          <n-space vertical>
            <n-alert type="info">
              导出数据库备份，可以在其他服务器或数据库之间迁移数据
            </n-alert>
            
            <n-space>
              <n-button @click="exportSQLite">
                <template #icon>
                  <n-icon><Download /></n-icon>
                </template>
                导出 SQLite 文件
              </n-button>
              <n-button @click="exportMySQL">
                <template #icon>
                  <n-icon><Code /></n-icon>
                </template>
                导出 MySQL SQL
              </n-button>
              <n-button @click="exportPostgreSQL">
                <template #icon>
                  <n-icon><Code /></n-icon>
                </template>
                导出 PostgreSQL SQL
              </n-button>
            </n-space>
          </n-space>
        </n-card>
        
        <n-card title="数据库导入" style="margin-top: 20px;">
          <n-space vertical>
            <n-alert type="warning">
              导入数据库将覆盖当前数据，原数据库会自动备份。导入SQLite文件(.db)会直接替换整个数据库，导入SQL文件(.sql)会执行SQL语句。
            </n-alert>
            
            <n-space>
              <n-upload
                accept=".db,.sqlite,.sql"
                :show-file-list="false"
                :custom-request="handleImport"
              >
                <n-button>
                  <template #icon>
                    <n-icon><CloudUpload /></n-icon>
                  </template>
                  选择文件导入
                </n-button>
              </n-upload>
            </n-space>
            
            <n-progress
              v-if="importing"
              type="line"
              :percentage="100"
              :indeterminate="true"
              status="info"
            />
          </n-space>
        </n-card>
      </n-tab-pane>

      <!-- LLM Tab -->
      <n-tab-pane name="llm" tab="AI 大模型">
        <div class="llm-container">
          <!-- Left Panel: Configuration -->
          <div class="llm-config-panel">
            <n-card title="AI 提供商配置" size="small">
              <n-space vertical :size="12">
                <n-alert type="info" :show-icon="false">
                  配置 AI 大模型服务，用于性能分析和智能对话
                </n-alert>
                
                <!-- Current Status -->
                <n-descriptions :column="1" bordered label-placement="left" size="small">
                  <n-descriptions-item label="当前提供商">
                    <n-tag type="primary">{{ currentProvider?.name || '未配置' }}</n-tag>
                  </n-descriptions-item>
                  <n-descriptions-item label="当前模型">
                    <n-tag type="info">{{ llmConfig.model || '默认' }}</n-tag>
                  </n-descriptions-item>
                  <n-descriptions-item label="连接状态">
                    <n-tag v-if="llmStatus === 'ok'" type="success">已连接</n-tag>
                    <n-tag v-else-if="llmStatus === 'error'" type="error">连接失败</n-tag>
                    <n-tag v-else type="warning">未测试</n-tag>
                  </n-descriptions-item>
                </n-descriptions>
                
                <n-divider>选择提供商</n-divider>
                
                <!-- Provider Selection -->
                <n-radio-group v-model:value="llmConfig.provider" name="provider">
                  <n-space vertical>
                    <n-radio v-for="provider in providers" :key="provider.id" :value="provider.id">
                      <n-space align="center" :size="4">
                        <span>{{ provider.name }}</span>
                        <n-tag v-if="provider.free" size="small" type="success">免费</n-tag>
                      </n-space>
                    </n-radio>
                  </n-space>
                </n-radio-group>
                
                <!-- API Key Input -->
                <n-divider>API 配置</n-divider>
                
                <n-form-item label="API Key">
                  <n-input
                    v-model:value="llmConfig.api_key"
                    type="password"
                    show-password-on="click"
                    placeholder="输入 API Key (留空使用默认配置)"
                  />
                </n-form-item>
                
                <n-form-item label="模型 ID">
                  <n-space vertical :size="4">
                    <n-input
                      v-model:value="llmConfig.model"
                      placeholder="自定义模型 ID，如: meta/llama-3.1-8b-instruct"
                    />
                    <n-text depth="3" style="font-size: 12px;">
                      当前提供商可用模型: {{ currentProvider?.models?.join(', ') }}
                    </n-text>
                  </n-space>
                </n-form-item>
                
                <n-space>
                  <n-button type="primary" @click="saveLLMConfig" :loading="savingConfig">
                    保存配置
                  </n-button>
                  <n-button @click="testCurrentProvider" :loading="testingProvider">
                    测试连接
                  </n-button>
                </n-space>
              </n-space>
            </n-card>
          </div>
          
          <!-- Right Panel: Chat -->
          <div class="llm-chat-panel">
            <n-card title="AI 对话助手" class="chat-card">
              <!-- Chat Messages -->
              <div class="chat-messages" ref="chatContainer">
                <div v-if="chatMessages.length === 0" class="chat-empty">
                  <n-empty description="开始与 AI 对话吧">
                    <template #extra>
                      <n-text depth="3">AI 会记住对话上下文</n-text>
                    </template>
                  </n-empty>
                </div>
                <div
                  v-for="msg in chatMessages"
                  :key="msg.id"
                  class="chat-message"
                  :class="msg.role"
                >
                  <div class="message-avatar">
                    <n-avatar round size="small">
                      {{ msg.role === 'user' ? '你' : 'AI' }}
                    </n-avatar>
                  </div>
                  <div class="message-content">
                    <div class="message-header">
                      <n-text strong>{{ msg.role === 'user' ? '你' : currentProvider?.name || 'AI' }}</n-text>
                      <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                        {{ formatTime(msg.created_at) }}
                      </n-text>
                    </div>
                    <n-text>{{ msg.content }}</n-text>
                  </div>
                </div>
                <div v-if="sendingMessage" class="chat-message assistant">
                  <div class="message-avatar">
                    <n-avatar round size="small" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">AI</n-avatar>
                  </div>
                  <div class="typing-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>
              
              <!-- Chat Input -->
              <div class="chat-input">
                <n-input
                  v-model:value="chatInput"
                  type="textarea"
                  placeholder="输入消息... (Shift+Enter 换行)"
                  :rows="2"
                  :disabled="sendingMessage"
                  @keydown.enter.exact.prevent="sendChatMessage"
                />
                <n-space style="margin-top: 8px;">
                  <n-button type="primary" @click="sendChatMessage" :loading="sendingMessage" :disabled="!chatInput">
                    发送
                  </n-button>
                  <n-button @click="clearChat" :disabled="chatMessages.length === 0">
                    清除对话
                  </n-button>
                  <n-text depth="3" style="font-size: 12px;">
                    按 Enter 发送，模型: {{ llmConfig.model || currentProvider?.default_model }}
                  </n-text>
                </n-space>
              </div>
            </n-card>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, nextTick } from 'vue'
import { NButton, NCard, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NSelect, NTabs, NTabPane, NSpace, NAlert, NIcon, useMessage, NDescriptions, NDescriptionsItem, NTag, NDivider, NCheckbox, NText, NRadio, NRadioGroup, NAvatar, NEmpty } from 'naive-ui'
import { FeatureCard, featureCardApi } from '@/api/featureCards'
import { dbApi } from '@/api/database'
import { getProviders, chat, testLLM, type LLMProvider } from '@/api/llm'
import { getLLMConfig, saveLLMConfig as saveConfigAPI, testProvider, getChatHistory, sendChatMessage as sendMessageAPI, clearChatHistory } from '@/api/llmConfig'
import {
  Desktop,
  People,
  Apps,
  Code,
  List,
  Play,
  GitCompare,
  StatsChart,
  Download,
  Create,
  Trash,
  Eye,
  EyeOff,
  CloudUpload,
  Chatbubbles,
  Settings,
  Sparkles,
  Send,
  Refresh,
  CheckmarkCircle,
  CloseCircle,
  Warning
} from '@vicons/ionicons5'

const message = useMessage()

// Data
const cards = ref<FeatureCard[]>([])
const showAddModal = ref(false)
const editingCard = ref<FeatureCard | null>(null)
const saving = ref(false)
const importing = ref(false)
const formRef = ref()

const formData = ref({
  card_key: '',
  title: '',
  description: '',
  icon: '',
  route: '',
  is_visible: true
})

const rules = {
  card_key: { required: true, message: '请输入卡片标识', trigger: 'blur' },
  title: { required: true, message: '请输入标题', trigger: 'blur' },
}

// LLM Data
const providers = ref<LLMProvider[]>([])
const currentProvider = ref<LLMProvider | null>(null)
const llmConfig = ref({
  provider: 'siliconflow',
  api_key: '',
  model: ''
})
const llmStatus = ref<'ok' | 'error' | 'untested'>('untested')
const testingProvider = ref<boolean>(false)
const savingConfig = ref(false)

// Chat Data
const chatMessages = ref<any[]>([])
const chatInput = ref('')
const sendingMessage = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

// Use fixed session ID stored in localStorage
const getSessionId = () => {
  let sid = localStorage.getItem('llm_session_id')
  if (!sid) {
    sid = 'default-session'
    localStorage.setItem('llm_session_id', sid)
  }
  return sid
}
const sessionId = ref(getSessionId())

// Load LLM config from backend
async function loadLLMConfig() {
  try {
    const config = await getLLMConfig()
    if (config.provider) {
      llmConfig.value.provider = config.provider
    }
    if (config.model) {
      llmConfig.value.model = config.model
    }
    // Load saved status
    if (config.status) {
      llmStatus.value = config.status as 'ok' | 'error' | 'untested'
    }
    // Don't load API key to frontend for security
    currentProvider.value = providers.value.find(p => p.id === llmConfig.value.provider) || null
    
    // Load chat history
    await loadChatHistory()
  } catch (e) {
    console.error('Failed to load LLM config:', e)
  }
}

// Save LLM config to backend
async function saveLLMConfig() {
  try {
    savingConfig.value = true
    await saveConfigAPI({
      provider: llmConfig.value.provider,
      api_key: llmConfig.value.api_key || undefined,
      model: llmConfig.value.model || undefined,
      is_active: true
    })
    currentProvider.value = providers.value.find(p => p.id === llmConfig.value.provider) || null
    message.success('配置已保存')
    
    // Reload config to get updated status
    await loadLLMConfig()
  } catch (e: any) {
    message.error('保存失败: ' + (e.message || e))
  } finally {
    savingConfig.value = false
  }
}

// Test current provider connection
async function testCurrentProvider() {
  testingProvider.value = true
  llmStatus.value = 'untested'
  try {
    const result = await testProvider(
      llmConfig.value.provider,
      llmConfig.value.api_key || undefined,
      llmConfig.value.model || undefined
    )
    if (result.status === 'ok') {
      llmStatus.value = 'ok'
      message.success(`连接成功! 模型: ${result.model}`)
    } else {
      llmStatus.value = 'error'
      message.error('连接失败: ' + result.error)
    }
    // Reload config to get saved status
    await loadLLMConfig()
  } catch (e: any) {
    llmStatus.value = 'error'
    message.error('测试失败: ' + (e.message || e))
  } finally {
    testingProvider.value = false
  }
}

// Load chat history
async function loadChatHistory() {
  try {
    chatMessages.value = await getChatHistory(sessionId.value)
    scrollToBottom()
  } catch (e) {
    console.error('Failed to load chat history:', e)
  }
}

// Send chat message
async function sendChatMessage() {
  if (!chatInput.value.trim() || sendingMessage.value) return
  
  const userMessage = chatInput.value.trim()
  chatInput.value = ''
  sendingMessage.value = true
  
  // Add user message immediately to UI
  chatMessages.value.push({
    id: `temp_${Date.now()}`,
    role: 'user',
    content: userMessage,
    created_at: new Date().toISOString()
  })
  scrollToBottom()
  
  try {
    const result = await sendMessageAPI(sessionId.value, {
      role: 'user',
      content: userMessage,
      model: llmConfig.value.model || currentProvider.value?.default_model,
      provider: llmConfig.value.provider
    })
    
    // Reload chat history
    await loadChatHistory()
  } catch (e: any) {
    message.error('发送失败: ' + (e.message || e))
    // Remove the temp message on error
    chatMessages.value = chatMessages.value.filter(m => !m.id?.startsWith('temp_'))
  } finally {
    sendingMessage.value = false
  }
}

// Clear chat history
async function clearChat() {
  try {
    await clearChatHistory(sessionId.value)
    chatMessages.value = []
    message.success('对话已清除')
  } catch (e: any) {
    message.error('清除失败: ' + (e.message || e))
  }
}

// Scroll to bottom of chat
function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// Format time
function formatTime(timeStr: string) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Load LLM providers
async function loadLLMProviders() {
  try {
    providers.value = await getProviders()
    // Load config after providers
    await loadLLMConfig()
  } catch (e) {
    message.error('加载 AI 提供商失败')
  }
}

// Icon options
const iconOptions = [
  { label: 'Desktop (设备)', value: 'desktop' },
  { label: 'People (人员)', value: 'people' },
  { label: 'Apps (应用)', value: 'apps' },
  { label: 'Code (代码)', value: 'code' },
  { label: 'List (列表)', value: 'list' },
  { label: 'Play (播放)', value: 'play' },
  { label: 'GitCompare (对比)', value: 'git-compare' },
  { label: 'Stats (统计)', value: 'stats' },
  { label: 'Settings (设置)', value: 'settings' },
  { label: 'Security (安全)', value: 'security' },
  { label: 'Analytics (分析)', value: 'analytics' },
  { label: 'Cloud (云)', value: 'cloud' },
]

// Table columns
const columns = [
  {
    title: '图标',
    key: 'icon',
    width: 80,
    render: (row: FeatureCard) => {
      const icons: Record<string, any> = {
        'desktop': Desktop,
        'people': People,
        'apps': Apps,
        'code': Code,
        'list': List,
        'play': Play,
        'git-compare': GitCompare,
        'stats': StatsChart,
      }
      return h(NIcon, { size: 24 }, { default: () => h(icons[row.icon || 'apps'] || Apps) })
    }
  },
  {
    title: '标题',
    key: 'title'
  },
  {
    title: '描述',
    key: 'description'
  },
  {
    title: '标识',
    key: 'card_key'
  },
  {
    title: '状态',
    key: 'is_visible',
    width: 100,
    render: (row: FeatureCard) => row.is_visible ? '显示' : '隐藏'
  },
  {
    title: '类型',
    key: 'is_custom',
    width: 80,
    render: (row: FeatureCard) => row.is_custom ? '自定义' : '系统'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: FeatureCard) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { 
          size: 'small', 
          onClick: () => editCard(row) 
        }, { default: () => '编辑' }),
        h(NButton, { 
          size: 'small', 
          onClick: () => toggleVisibility(row),
          disabled: !row.is_custom && row.card_key === 'devices' // 至少保留设备管理
        }, { default: () => row.is_visible ? '隐藏' : '显示' }),
        !row.is_custom ? null : h(NButton, { 
          size: 'small', 
          type: 'error',
          onClick: () => deleteCard(row),
          disabled: row.card_key === 'devices' // 不能删除设备管理
        }, { default: () => '删除' })
      ].filter(Boolean)
    })
  }
]

// Load cards
const loadCards = async () => {
  try {
    const res = await featureCardApi.list()
    cards.value = res.data.items
  } catch (e) {
    message.error('加载失败')
  }
}

// Edit card
const editCard = (card: FeatureCard) => {
  editingCard.value = card
  formData.value = {
    card_key: card.card_key,
    title: card.title,
    description: card.description || '',
    icon: card.icon || '',
    route: card.route || '',
    is_visible: card.is_visible
  }
  showAddModal.value = true
}

// Save card
const saveCard = async () => {
  try {
    saving.value = true
    
    if (editingCard.value) {
      await featureCardApi.update(editingCard.value.id, {
        title: formData.value.title,
        description: formData.value.description,
        icon: formData.value.icon,
        route: formData.value.route,
        is_visible: formData.value.is_visible
      })
      message.success('更新成功')
    } else {
      await featureCardApi.create({
        card_key: formData.value.card_key,
        title: formData.value.title,
        description: formData.value.description,
        icon: formData.value.icon,
        route: formData.value.route,
        is_visible: formData.value.is_visible
      })
      message.success('创建成功')
    }
    
    showAddModal.value = false
    loadCards()
    editingCard.value = null
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Toggle visibility
const toggleVisibility = async (card: FeatureCard) => {
  try {
    await featureCardApi.update(card.id, { is_visible: !card.is_visible })
    message.success(card.is_visible ? '已隐藏' : '已显示')
    loadCards()
  } catch (e) {
    message.error('操作失败')
  }
}

// Delete card
const deleteCard = async (card: FeatureCard) => {
  try {
    await featureCardApi.delete(card.id)
    message.success('删除成功')
    loadCards()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

// Export functions
const getApiBase = () => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
}

const exportSQLite = () => {
  window.open(`${getApiBase()}/db/export/sqlite`, '_blank')
}

const exportMySQL = () => {
  window.open(`${getApiBase()}/db/export/mysql`, '_blank')
}

const exportPostgreSQL = () => {
  window.open(`${getApiBase()}/db/export/postgresql`, '_blank')
}

// Import database
const handleImport = async ({ file }: { file: any }) => {
  try {
    importing.value = true
    const res = await dbApi.importDB(file.file)
    
    if (res.success) {
      message.success(res.message || '导入成功')
    } else {
      message.error(res.detail || '导入失败')
    }
  } catch (e: any) {
    message.error(e.response?.data?.detail || e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// Reset form when modal closes
const resetForm = () => {
  editingCard.value = null
  formData.value = {
    card_key: '',
    title: '',
    description: '',
    icon: '',
    route: '',
    is_visible: true
  }
}

onMounted(() => {
  loadCards()
  loadLLMProviders()
})

// Watch modal close
import { watch } from 'vue'
watch(showAddModal, (val) => {
  if (!val) resetForm()
})
</script>

<style scoped lang="scss">
// Design tokens based on ui-ux-pro-max guidelines
$primary-color: #0ea5e9;
$primary-hover: #0284c7;
$bg-user-message: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
$bg-assistant-message: #ffffff;
$border-color: #e2e8f0;
$text-primary: #1e293b;
$text-secondary: #64748b;
$text-muted: #94a3b8;
$bg-input: #f8fafc;
$shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
$shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
$radius-sm: 8px;
$radius-md: 12px;
$radius-lg: 16px;
$transition: all 0.2s ease;

.system-management {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .page-header {
    margin-bottom: 24px;
    
    h1 {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 8px 0;
    }
    
    p {
      color: #666;
      margin: 0;
    }
  }
  
  .toolbar {
    margin-bottom: 16px;
  }
  
  // LLM Container - Left-Right Layout
  .llm-container {
    display: flex;
    gap: 20px;
    height: calc(100vh - 200px);
    min-height: 520px;
  }
  
  // Left Panel - Config
  .llm-config-panel {
    width: 340px;
    flex-shrink: 0;
    overflow-y: auto;
    
    :deep(.n-card) {
      border-radius: $radius-md;
      box-shadow: $shadow-sm;
      border: 1px solid $border-color;
    }
    
    :deep(.n-form-item .n-form-item-label) {
      font-weight: 500;
      color: $text-primary;
    }
  }
  
  // Right Panel - Chat
  .llm-chat-panel {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    
    .chat-card {
      height: 100%;
      border-radius: $radius-lg;
      box-shadow: $shadow-md;
      border: 1px solid $border-color;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: #fff;
      
      :deep(.n-card-header) {
        padding: 16px 20px;
        border-bottom: 1px solid $border-color;
        background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
        
        .n-card-header__main {
          font-weight: 600;
          color: $text-primary;
        }
      }
      
      :deep(.n-card__content) {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        padding: 0 !important;
      }
    }
  }
  
  // Chat Messages Area
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
  }
  
  .chat-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: $text-muted;
    gap: 8px;
  }
  
  // Chat Message Bubble
  .chat-message {
    display: flex;
    gap: 12px;
    max-width: 80%;
    animation: messageIn 0.3s ease;
    
    @keyframes messageIn {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    &.user {
      align-self: flex-end;
      flex-direction: row-reverse;
      
      .message-avatar {
        .n-avatar {
          background: $primary-color;
          color: #fff;
          font-weight: 600;
        }
      }
      
      .message-content {
        background: $bg-user-message;
        color: #fff;
        border-radius: $radius-lg $radius-lg 4px $radius-lg;
        box-shadow: $shadow-sm;
        
        .message-header {
          color: rgba(255, 255, 255, 0.9);
          
          .n-text {
            color: rgba(255, 255, 255, 0.9) !important;
          }
        }
      }
    }
    
    &.assistant {
      align-self: flex-start;
      
      .message-avatar {
        .n-avatar {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: #fff;
          font-weight: 600;
        }
      }
      
      .message-content {
        background: $bg-assistant-message;
        border: 1px solid $border-color;
        border-radius: $radius-lg $radius-lg $radius-lg 4px;
        box-shadow: $shadow-sm;
        
        .message-header {
          color: $text-secondary;
        }
      }
    }
    
    .message-avatar {
      flex-shrink: 0;
    }
    
    .message-content {
      padding: 14px 18px;
      min-width: 120px;
      line-height: 1.6;
      
      .message-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 13px;
      }
    }
  }
  
  // Typing Indicator
  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 14px 18px;
    background: $bg-assistant-message;
    border: 1px solid $border-color;
    border-radius: $radius-lg $radius-lg $radius-lg 4px;
    
    .dot {
      width: 8px;
      height: 8px;
      background: $text-muted;
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out;
      
      &:nth-child(1) { animation-delay: 0s; }
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
    
    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40% { transform: scale(1); opacity: 1; }
    }
  }
  
  // Chat Input Area
  .chat-input {
    padding: 16px 20px;
    border-top: 1px solid $border-color;
    background: #fff;
    
    :deep(.n-input) {
      border-radius: $radius-md;
      
      .n-input__border {
        border-color: $border-color;
      }
      
      &:focus-within {
        border-color: $primary-color;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
      }
    }
    
    .chat-input-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 10px;
    }
  }
  
  // Responsive
  @media (max-width: 1024px) {
    .llm-container {
      flex-direction: column;
      height: auto;
    }
    
    .llm-config-panel {
      width: 100%;
      max-height: 300px;
    }
    
    .llm-chat-panel {
      min-height: 500px;
    }
  }
}
</style>
