<template>
  <div class="standard-manage-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><Construct /></n-icon>
          <n-h1 class="title">标准管理</n-h1>
        </div>
      </div>
    </div>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="standards"
        :loading="loading"
        :bordered="false"
        class="standard-table"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { NCard, NH1, NDataTable, NTag, NButton, NSpace, NIcon } from 'naive-ui'
import { Pencil, Trash, Construct } from '@vicons/ionicons5'

const standards = ref([
  {
    id: '1',
    position_name: '开发工程师',
    position_code: 'DEV',
    cpu_min_cores: 8,
    cpu_min_threads: 16,
    ram_min_gb: 32,
    gpu_min_vram_mb: 8192,
    is_active: true
  },
  {
    id: '2',
    position_name: 'UI设计师',
    position_code: 'DESIGN',
    cpu_min_cores: 6,
    cpu_min_threads: 12,
    ram_min_gb: 16,
    gpu_min_vram_mb: 4096,
    is_active: true
  },
  {
    id: '3',
    position_name: 'QA工程师',
    position_code: 'QA',
    cpu_min_cores: 4,
    cpu_min_threads: 8,
    ram_min_gb: 16,
    gpu_min_vram_mb: 2048,
    is_active: true
  }
])

const loading = ref(false)

const columns = computed(() => [
  { title: '岗位名称', key: 'position_name' },
  { title: '编码', key: 'position_code' },
  { title: '最低CPU核心数', key: 'cpu_min_cores' },
  { title: '最低线程数', key: 'cpu_min_threads' },
  { title: '最低内存(GB)', key: 'ram_min_gb' },
  { title: '最低显存(MB)', key: 'gpu_min_vram_mb' },
  {
    title: '状态',
    key: 'is_active',
    render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, () => row.is_active ? '启用' : '禁用')
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: () => h(NSpace, { size: 'small' }, () => [
      h(NButton, { size: 'small' }, () => h(NIcon, null, () => h(Pencil))),
      h(NButton, { size: 'small' }, () => h(NIcon, null, () => h(Trash)))
    ])
  }
])
</script>

<style scoped>
.standard-manage-page {
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

/* Table Card */
.table-card {
  margin: 20px 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.standard-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.standard-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.standard-table :deep(.n-data-table-td) {
  padding: 12px 16px;
}
</style>
