<template>
  <div class="standard-manage">
    <n-h1>标准管理</n-h1>
    
    <n-card>
      <n-data-table
        :columns="columns"
        :data="standards"
        :loading="loading"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { NCard, NH1, NDataTable, NTag, NButton, NSpace, NIcon } from 'naive-ui'
import { Pencil, Trash } from '@vicons/ionicons5'

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
.standard-manage {
  padding: 20px;
}
</style>
