<template>
  <div class="device-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><Desktop /></n-icon>
          <n-h1 class="title">设备管理</n-h1>
        </div>
        <n-button type="primary" class="add-btn" @click="showAddModal = true">
          <template #icon><n-icon><Add /></n-icon></template>
          添加设备
        </n-button>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-input 
          v-model:value="filters.keyword" 
          placeholder="搜索设备名称、IP、MAC..." 
          clearable 
          class="search-input" 
        />
        <n-select 
          v-model:value="filters.status" 
          placeholder="设备状态" 
          :options="statusOptions" 
          clearable 
          class="status-select" 
        />
        <n-select 
          v-model:value="filters.department" 
          placeholder="所属部门" 
          :options="deptOptions" 
          clearable 
          class="dept-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadDevices">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="devices"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Device) => row.id"
        :bordered="false"
        class="device-table"
      />
    </n-card>
    
    <!-- Add/Edit Modal -->
    <n-modal v-model:show="showAddModal" preset="card" title="添加新设备" style="width: 600px" class="custom-modal">
      <n-form ref="formRef" :model="deviceForm" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="设备名称" path="device_name">
          <n-input v-model:value="deviceForm.device_name" placeholder="请输入设备名称" />
        </n-form-item>
        <n-form-item label="MAC地址" path="mac_address">
          <n-input v-model:value="deviceForm.mac_address" placeholder="AA:BB:CC:DD:EE:FF" />
        </n-form-item>
        <n-form-item label="IP地址" path="ip_address">
          <n-input v-model:value="deviceForm.ip_address" placeholder="192.168.1.100" />
        </n-form-item>
        <n-form-item label="主机名" path="hostname">
          <n-input v-model:value="deviceForm.hostname" placeholder="WORKSTATION-01" />
        </n-form-item>
        <n-form-item label="所属部门" path="department">
          <n-input v-model:value="deviceForm.department" placeholder="研发部" />
        </n-form-item>
        <n-form-item label="岗位" path="position">
          <n-input v-model:value="deviceForm.position" placeholder="软件开发" />
        </n-form-item>
        <n-form-item label="分配给" path="assigned_to">
          <n-input v-model:value="deviceForm.assigned_to" placeholder="张三" />
        </n-form-item>
        <n-form-item label="备注" path="notes">
          <n-input v-model:value="deviceForm.notes" type="textarea" placeholder="其他说明信息..." />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddDevice" :loading="saving">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  NCard, NH1, NButton, NSpace, NInput, NSelect, NDataTable, NModal, NForm, NFormItem, NIcon, NTag, NPopconfirm 
} from 'naive-ui'
import { Add, Trash, Pencil, Eye, Search, Desktop } from '@vicons/ionicons5'
import { deviceApi, type Device, type DeviceCreate, type DeviceParams } from '@/api/devices'

const { t } = useI18n()
const router = useRouter()

const devices = ref<Device[]>([])
const loading = ref(false)
const saving = ref(false)
const showAddModal = ref(false)

const filters = reactive<DeviceParams>({
  page: 1,
  page_size: 20,
  keyword: '',
  status: undefined,
  department: undefined
})

const deviceForm = reactive<DeviceCreate>({
  device_name: '',
  mac_address: '',
  ip_address: '',
  hostname: '',
  department: '',
  position: '',
  assigned_to: '',
  notes: ''
})

const rules = {
  device_name: { required: true, message: 'Device name is required' },
  mac_address: { required: true, message: 'MAC address is required' }
}

const statusOptions = [
  { label: 'Online', value: 'online' },
  { label: 'Offline', value: 'offline' },
  { label: 'Testing', value: 'testing' },
  { label: 'Error', value: 'error' }
]

const deptOptions = [
  { label: 'Development', value: 'Development' },
  { label: 'Design', value: 'Design' },
  { label: 'QA', value: 'QA' },
  { label: 'Operations', value: 'Operations' }
]

const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  itemCount: 0,
  onChange: (page: number) => {
    filters.page = page
    loadDevices()
  },
  onUpdatePageSize: (pageSize: number) => {
    filters.page_size = pageSize
    loadDevices()
  }
})

const columns = computed(() => [
  { 
    title: '状态', 
    key: 'status',
    width: 100,
    render: (row: Device) => {
      const statusText = row.status === 'online' ? '在线' : row.status === 'testing' ? '测试中' : row.status === 'offline' ? '离线' : row.status
      const tagType = row.status === 'online' ? 'success' : row.status === 'testing' ? 'warning' : 'default'
      return h(NTag, { type: tagType, size: 'small' }, () => statusText)
    }
  },
  { title: '设备名称', key: 'device_name' },
  { title: 'IP地址', key: 'ip_address' },
  { title: '部门', key: 'department' },
  { title: '岗位', key: 'position' },
  { title: 'CPU', key: 'cpu_model', ellipsis: { tooltip: true } },
  { title: 'GPU', key: 'gpu_model', ellipsis: { tooltip: true } },
  { 
    title: '最后在线', 
    key: 'last_seen_at',
    render: (row: Device) => row.last_seen_at ? new Date(row.last_seen_at).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Device) => h(NSpace, { size: 'small' }, () => [
      h(NButton, { size: 'small', onClick: () => router.push(`/devices/${row.id}`) }, () => h(NIcon, null, () => h(Eye))),
      h(NButton, { size: 'small', onClick: () => handleDelete(row.id) }, () => h(NIcon, null, () => h(Trash)))
    ])
  }
])

const loadDevices = async () => {
  loading.value = true
  try {
    const res = await deviceApi.list(filters)
    devices.value = res.data.items
    pagination.value.itemCount = res.data.total
  } catch (error) {
    console.error('Failed to load devices:', error)
  } finally {
    loading.value = false
  }
}

const handleAddDevice = async () => {
  saving.value = true
  try {
    await deviceApi.create(deviceForm)
    showAddModal.value = false
    loadDevices()
    Object.assign(deviceForm, { device_name: '', mac_address: '', ip_address: '', hostname: '', department: '', position: '', assigned_to: '', notes: '' })
  } catch (error) {
    console.error('Failed to add device:', error)
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await deviceApi.delete(id)
    loadDevices()
  } catch (error) {
    console.error('Failed to delete device:', error)
  }
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.device-list-page {
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

.search-input {
  flex: 1;
  max-width: 280px;
}

.status-select,
.dept-select {
  width: 150px;
}

.search-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
  color: #000;
}

/* Table Card */
.table-card {
  margin: 0 24px 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.device-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.device-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.device-table :deep(.n-data-table-td) {
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-footer .n-button:last-child {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 8px;
}
</style>
