<template>
  <div class="result-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><DocumentText /></n-icon>
          <n-h1 class="title">测试结果</n-h1>
        </div>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-select 
          v-model:value="filters.test_status" 
          placeholder="测试状态" 
          :options="statusOptions" 
          clearable 
          class="status-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadResults">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="results"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: TestResult) => row.id"
        :bordered="false"
        class="result-table"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NH1, NButton, NSpace, NSelect, NDataTable, NTag, NIcon } from 'naive-ui'
import { Eye, DocumentText, Search } from '@vicons/ionicons5'
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
.result-list-page {
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

.status-select {
  width: 150px;
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

.result-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.result-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.result-table :deep(.n-data-table-td) {
  padding: 12px 16px;
}
</style>
