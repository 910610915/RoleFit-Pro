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
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NButton, NCard, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NSelect, NTabs, NTabPane, NSpace, NAlert, NIcon, useMessage } from 'naive-ui'
import { FeatureCard, featureCardApi } from '@/api/featureCards'
import { dbApi } from '@/api/database'
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
  CloudUpload
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
})

// Watch modal close
import { watch } from 'vue'
watch(showAddModal, (val) => {
  if (!val) resetForm()
})
</script>

<style scoped lang="scss">
.system-management {
  padding: 24px;
  
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
}
</style>
