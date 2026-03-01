<template>
  <div class="task-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><List /></n-icon>
          <n-h1 class="title">任务管理</n-h1>
        </div>
        <n-button type="primary" class="add-btn" @click="router.push('/tasks/create')">
          <template #icon><n-icon><Add /></n-icon></template>
          创建任务
        </n-button>
      </div>
    </div>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: TestTask) => row.id"
        :bordered="false"
        class="task-table"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NH1, NButton, NSpace, NDataTable, NTag, NIcon } from 'naive-ui'
import { Add, Play, Stop, List } from '@vicons/ionicons5'
import { taskApi, type TestTask } from '@/api/tasks'

const router = useRouter()

const tasks = ref<TestTask[]>([])
const loading = ref(false)

const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  itemCount: 0,
  onChange: (page: number) => {
    loadTasks(page)
  }
})

const statusColors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  running: 'primary',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning'
}

const statusText: Record<string, string> = {
  pending: '待执行',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消'
}

const columns = computed(() => [
  { title: '任务名称', key: 'task_name' },
  { title: '类型', key: 'task_type' },
  { 
    title: '状态', 
    key: 'task_status',
    render: (row: TestTask) => h(NTag, { type: statusColors[row.task_status] || 'default', size: 'small' }, () => statusText[row.task_status] || row.task_status)
  },
  { 
    title: '创建时间', 
    key: 'created_at',
    render: (row: TestTask) => new Date(row.created_at).toLocaleString()
  },
  { 
    title: '开始时间', 
    key: 'started_at',
    render: (row: TestTask) => row.started_at ? new Date(row.started_at).toLocaleString() : '-'
  },
  { 
    title: '完成时间', 
    key: 'completed_at',
    render: (row: TestTask) => row.completed_at ? new Date(row.completed_at).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: TestTask) => h(NSpace, { size: 'small' }, () => [
      row.task_status === 'pending' ? h(NButton, { size: 'small', onClick: () => handleExecute(row.id) }, () => h(NIcon, null, () => h(Play))) : null,
      row.task_status === 'running' ? h(NButton, { size: 'small', onClick: () => handleCancel(row.id) }, () => h(NIcon, null, () => h(Stop))) : null
    ])
  }
])

const loadTasks = async (page = 1) => {
  loading.value = true
  try {
    const res = await taskApi.list({ page, page_size: 20 })
    tasks.value = res.data.items
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    loading.value = false
  }
}

const handleExecute = async (id: string) => {
  try {
    await taskApi.execute(id, [])
    loadTasks()
  } catch (error) {
    console.error('Failed to execute task:', error)
  }
}

const handleCancel = async (id: string) => {
  try {
    await taskApi.cancel(id)
    loadTasks()
  } catch (error) {
    console.error('Failed to cancel task:', error)
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-list-page {
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

.add-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 10px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
  color: #000;
}

.add-btn:hover {
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
  transform: translateY(-1px);
}

/* Table Card */
.table-card {
  margin: 20px 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.task-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.task-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.task-table :deep(.n-data-table-td) {
  padding: 12px 16px;
}
</style>
