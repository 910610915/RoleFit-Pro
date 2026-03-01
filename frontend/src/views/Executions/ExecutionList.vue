<template>
  <div class="execution-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><Time /></n-icon>
          <n-h1 class="title">执行记录</n-h1>
        </div>
        <n-button type="primary" class="refresh-btn" @click="refreshData">
          <template #icon><n-icon><Refresh /></n-icon></template>
          刷新
        </n-button>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-select 
          v-model:value="filters.device_id" 
          placeholder="选择设备" 
          :options="deviceOptions" 
          clearable 
          class="filter-select" 
        />
        <n-select 
          v-model:value="filters.script_id" 
          placeholder="选择脚本" 
          :options="scriptOptions" 
          clearable 
          class="filter-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadExecutions">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="executions"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Execution) => row.id"
        :bordered="false"
        class="execution-table"
      />
    </n-card>
    
    <!-- Detail Modal -->
    <n-modal v-model:show="showDetail" preset="card" title="执行详情" style="width: 700px" class="custom-modal">
      <n-descriptions v-if="selectedExecution" label-placement="left" :column="2">
        <n-descriptions-item label="执行ID">{{ selectedExecution.id }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="selectedExecution.exit_code === 0 ? 'success' : 'error'" size="small">
            {{ selectedExecution.exit_code === 0 ? '成功' : '失败' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="开始时间">{{ formatTime(selectedExecution.start_time) }}</n-descriptions-item>
        <n-descriptions-item label="结束时间">{{ formatTime(selectedExecution.end_time) }}</n-descriptions-item>
        <n-descriptions-item label="执行时长">{{ selectedExecution.duration_seconds }}秒</n-descriptions-item>
        <n-descriptions-item label="Exit Code">{{ selectedExecution.exit_code }}</n-descriptions-item>
        <n-descriptions-item label="错误信息" :span="2">{{ selectedExecution.error_message || '-' }}</n-descriptions-item>
      </n-descriptions>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useMessage } from 'naive-ui'
import { 
  NCard, NH1, NButton, NSpace, NSelect, NDataTable, NModal, NDescriptions, NDescriptionsItem, NTag, NIcon 
} from 'naive-ui'
import { Refresh, Eye, PlayCircle, CheckmarkCircle, CloseCircle, Time, Search } from '@vicons/ionicons5'
import { executionApi, type Execution } from '@/api/executions'
import { deviceApi } from '@/api/devices'
import { scriptApi } from '@/api/scripts'

const message = useMessage()

const executions = ref<Execution[]>([])
const devices = ref<any[]>([])
const scripts = ref<any[]>([])
const loading = ref(false)
const showDetail = ref(false)
const selectedExecution = ref<Execution | null>(null)

const filters = reactive({
  page: 1,
  page_size: 20,
  device_id: undefined as string | undefined,
  script_id: undefined as string | undefined
})

// 设备选项
const deviceOptions = computed(() => 
  devices.value.map(d => ({ label: d.device_name, value: d.id }))
)

// 脚本选项
const scriptOptions = computed(() => 
  scripts.value.map(s => ({ label: s.script_name, value: s.id }))
)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  itemCount: 0,
  onChange: (page: number) => {
    filters.page = page
    loadExecutions()
  },
  onUpdatePageSize: (pageSize: number) => {
    filters.page_size = pageSize
    loadExecutions()
  }
})

const getDeviceName = (id: string | undefined) => {
  if (!id) return '-'
  const device = devices.value.find(d => d.id === id)
  return device ? device.device_name : id
}

const getScriptName = (id: string | undefined) => {
  if (!id) return '-'
  const script = scripts.value.find(s => s.id === id)
  return script ? script.script_name : id
}

const formatTime = (time: string | undefined) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const columns = computed(() => [
  {
    title: '脚本名称',
    key: 'script_id',
    width: 180,
    render: (row: Execution) => getScriptName(row.script_id)
  },
  {
    title: '设备',
    key: 'device_id',
    width: 150,
    render: (row: Execution) => getDeviceName(row.device_id)
  },
  {
    title: '开始时间',
    key: 'start_time',
    width: 180,
    render: (row: Execution) => formatTime(row.start_time)
  },
  {
    title: '执行时长',
    key: 'duration_seconds',
    width: 100,
    render: (row: Execution) => row.duration_seconds ? `${row.duration_seconds}秒` : '-'
  },
  {
    title: '状态',
    key: 'exit_code',
    width: 100,
    render: (row: Execution) => h(NTag, { 
      type: row.exit_code === 0 ? 'success' : (row.exit_code === -1 ? 'warning' : 'error'), 
      size: 'small' 
    }, { 
      default: () => row.exit_code === 0 ? '成功' : (row.exit_code === -1 ? '进行中' : '失败') 
    })
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row: Execution) => h(NButton, { size: 'small', onClick: () => showExecutionDetail(row) }, 
      { default: () => '详情' })
  }
])

const loadExecutions = async () => {
  loading.value = true
  try {
    const res = await executionApi.list(filters)
    executions.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (e: any) {
    message.error('加载执行记录失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadDevices = async () => {
  try {
    const res = await deviceApi.list({ page_size: 100 })
    devices.value = res.data.items
  } catch (e) {
    console.error('加载设备失败', e)
  }
}

const loadScripts = async () => {
  try {
    const res = await scriptApi.list({ page_size: 100 })
    scripts.value = res.data.items
  } catch (e) {
    console.error('加载脚本失败', e)
  }
}

const showExecutionDetail = (row: Execution) => {
  selectedExecution.value = row
  showDetail.value = true
}

const refreshData = () => {
  loadExecutions()
}

onMounted(() => {
  loadDevices()
  loadScripts()
  loadExecutions()
})
</script>

<style scoped>
.execution-list-page {
  padding: 0;
  min-height: 100%;
  background: #f8fafc;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title .title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
}

.refresh-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 10px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}

.refresh-btn:hover {
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
  transform: translateY(-1px);
}

/* Filter Card */
.filter-card {
  margin: 20px 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-card :deep(.n-card__content) {
  padding: 16px;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-select {
  width: 160px;
  border-radius: 8px;
}

.search-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}

/* Table Card */
.table-card {
  margin: 0 24px 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.execution-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.execution-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.execution-table :deep(.n-data-table-td) {
  padding: 12px 16px;
}

/* Modal */
.custom-modal :deep(.n-card) {
  border-radius: 16px;
}

.custom-modal :deep(.n-card-header__main) {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
</style>
