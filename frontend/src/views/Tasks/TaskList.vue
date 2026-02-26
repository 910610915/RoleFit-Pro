<template>
  <div class="task-list">
    <div class="header">
      <n-h1>任务管理</n-h1>
      <n-button type="primary" @click="router.push('/tasks/create')">
        <template #icon><n-icon><add /></n-icon></template>
        创建任务
      </n-button>
    </div>
    
    <n-card>
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: TestTask) => row.id"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NH1, NButton, NSpace, NDataTable, NTag, NIcon } from 'naive-ui'
import { Add, Play, Stop } from '@vicons/ionicons5'
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
.task-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
