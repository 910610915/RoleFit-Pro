<template>
  <div class="result-list">
    <n-h1>测试结果</n-h1>
    
    <n-card class="filter-card">
      <n-space>
        <n-select v-model:value="filters.test_status" placeholder="状态" :options="statusOptions" clearable style="width: 150px" />
        <n-button @click="loadResults">搜索</n-button>
      </n-space>
    </n-card>
    
    <n-card>
      <n-data-table
        :columns="columns"
        :data="results"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: TestResult) => row.id"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NH1, NButton, NSpace, NSelect, NDataTable, NTag, NIcon } from 'naive-ui'
import { Eye } from '@vicons/ionicons5'
import { resultApi, type TestResult, type ResultParams } from '@/api/results'

const router = useRouter()

const results = ref<TestResult[]>([])
const loading = ref(false)

const filters = reactive<ResultParams>({
  page: 1,
  page_size: 20,
  test_status: undefined
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  itemCount: 0,
  onChange: (page: number) => {
    filters.page = page
    loadResults()
  }
})

const statusOptions = [
  { label: '通过', value: 'passed' },
  { label: '失败', value: 'failed' },
  { label: '警告', value: 'warning' },
  { label: '部分通过', value: 'partial' }
]

const statusText: Record<string, string> = {
  passed: '通过',
  failed: '失败',
  warning: '警告',
  partial: '部分通过'
}

const getStatusText = (status: string | undefined) => {
  return status ? (statusText[status] || status) : '-'
}

const columns = computed(() => [
  { title: '设备名称', key: 'device_name' },
  { title: '测试类型', key: 'test_type' },
  { 
    title: '状态', 
    key: 'test_status',
    render: (row: TestResult) => h(NTag, { type: row.test_status === 'passed' ? 'success' : row.test_status === 'failed' ? 'error' : 'warning', size: 'small' }, () => getStatusText(row.test_status))
  },
  { title: '总分', key: 'overall_score' },
  { 
    title: '开始时间', 
    key: 'start_time',
    render: (row: TestResult) => new Date(row.start_time).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: TestResult) => h(NButton, { size: 'small', onClick: () => router.push(`/results/${row.id}`) }, () => h(NIcon, null, () => h(Eye)))
  }
])

const loadResults = async () => {
  loading.value = true
  try {
    const res = await resultApi.list(filters)
    results.value = res.data.items
    pagination.value.itemCount = res.data.total
  } catch (error) {
    console.error('Failed to load results:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.result-list {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}
</style>
