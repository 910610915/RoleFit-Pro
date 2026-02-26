<template>
  <div class="device-list">
    <div class="header">
      <n-h1>设备管理</n-h1>
      <n-button type="primary" @click="showAddModal = true">
        <template #icon><n-icon><add /></n-icon></template>
        添加设备
      </n-button>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <n-space>
        <n-input v-model:value="filters.keyword" placeholder="搜索..." clearable style="width: 200px" />
        <n-select v-model:value="filters.status" placeholder="状态" :options="statusOptions" clearable style="width: 150px" />
        <n-select v-model:value="filters.department" placeholder="部门" :options="deptOptions" clearable style="width: 150px" />
        <n-button @click="loadDevices">搜索</n-button>
      </n-space>
    </n-card>
    
    <!-- Table -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="devices"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Device) => row.id"
      />
    </n-card>
    
    <!-- Add/Edit Modal -->
    <n-modal v-model:show="showAddModal" preset="card" title="添加设备" style="width: 600px">
      <n-form ref="formRef" :model="deviceForm" :rules="rules">
        <n-form-item label="设备名称" path="device_name">
          <n-input v-model:value="deviceForm.device_name" />
        </n-form-item>
        <n-form-item label="MAC地址" path="mac_address">
          <n-input v-model:value="deviceForm.mac_address" placeholder="AA:BB:CC:DD:EE:FF" />
        </n-form-item>
        <n-form-item label="IP地址" path="ip_address">
          <n-input v-model:value="deviceForm.ip_address" />
        </n-form-item>
        <n-form-item label="主机名" path="hostname">
          <n-input v-model:value="deviceForm.hostname" />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="deviceForm.department" />
        </n-form-item>
        <n-form-item label="岗位" path="position">
          <n-input v-model:value="deviceForm.position" />
        </n-form-item>
        <n-form-item label="分配给" path="assigned_to">
          <n-input v-model:value="deviceForm.assigned_to" />
        </n-form-item>
        <n-form-item label="备注" path="notes">
          <n-input v-model:value="deviceForm.notes" type="textarea" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddDevice" :loading="saving">保存</n-button>
        </n-space>
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
import { Add, Trash, Pencil, Eye } from '@vicons/ionicons5'
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
.device-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}
</style>
