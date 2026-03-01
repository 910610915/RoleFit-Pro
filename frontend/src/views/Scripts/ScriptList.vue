<template>
  <div class="script-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><PlayCircle /></n-icon>
          <n-h1 class="title">岗位测试脚本</n-h1>
        </div>
        <n-button type="primary" class="add-btn" @click="openAddModal">
          <template #icon><n-icon><Add /></n-icon></template>
          添加脚本
        </n-button>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-select 
          v-model:value="filters.position_id" 
          placeholder="关联岗位" 
          :options="positionOptions" 
          clearable 
          class="filter-select" 
        />
        <n-select 
          v-model:value="filters.software_id" 
          placeholder="关联软件" 
          :options="softwareOptions" 
          clearable 
          class="filter-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadScripts">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="scripts"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Script) => row.id"
        :bordered="false"
        class="script-table"
      />
    </n-card>
    
    <!-- Add/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑脚本' : '添加新脚本'" style="width: 700px" class="custom-modal">
      <n-form ref="formRef" :model="scriptForm" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="脚本名称" path="script_name">
          <n-input v-model:value="scriptForm.script_name" placeholder="如：UE5项目启动测试" />
        </n-form-item>
        <n-form-item label="脚本代码" path="script_code">
          <n-input v-model:value="scriptForm.script_code" placeholder="如：UE5_START_TEST" :disabled="isEdit" />
        </n-form-item>
        <n-form-item label="关联岗位" path="position_ids">
          <n-select v-model:value="scriptForm.position_ids" :options="positionOptions" placeholder="选择岗位" multiple clearable />
        </n-form-item>
        <n-form-item label="关联软件" path="software_id">
          <n-select v-model:value="scriptForm.software_id" :options="softwareOptions" placeholder="选择软件" clearable />
        </n-form-item>
        <n-form-item label="脚本类型" path="script_type">
          <n-select v-model:value="scriptForm.script_type" :options="scriptTypeOptions" placeholder="选择类型" />
        </n-form-item>
        <n-form-item label="期望时长" path="expected_duration">
          <n-input-number v-model:value="scriptForm.expected_duration" :min="10" :max="36000" />
        </n-form-item>
        <n-form-item label="脚本内容" path="script_content">
          <n-input v-model:value="scriptForm.script_content" type="textarea" :rows="6" placeholder='JSON格式的脚本内容，如：{"action": "launch", "path": "C:\\UE5\\UE4Editor.exe"}' />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave" :loading="saving">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useMessage } from 'naive-ui'
import { 
  NCard, NH1, NButton, NSpace, NSelect, NDataTable, NModal, NForm, NFormItem, NIcon, NTag, NPopconfirm, NInputNumber 
} from 'naive-ui'
import { Add, Trash, Pencil, PlayCircle, Search } from '@vicons/ionicons5'
import { scriptApi, type Script } from '@/api/scripts'
import { positionApi } from '@/api/positions'
import { softwareApi } from '@/api/software'

const message = useMessage()

const scripts = ref<Script[]>([])
const positions = ref<any[]>([])
const softwareList = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)

const filters = reactive({
  page: 1,
  page_size: 20,
  position_id: undefined as string | undefined,
  software_id: undefined as string | undefined
})

const scriptForm = reactive({
  script_name: '',
  script_code: '',
  position_ids: [] as string[],
  software_id: undefined as string | undefined,
  script_type: '',
  script_content: '',
  expected_duration: 300
})

const rules = {
  script_name: { required: true, message: '请输入脚本名称' },
  script_code: { required: true, message: '请输入脚本代码' }
}

// 脚本类型选项
const scriptTypeOptions = [
  { label: '启动测试', value: 'START' },
  { label: '操作测试', value: 'OPERATION' },
  { label: '渲染测试', value: 'RENDER' },
  { label: '压力测试', value: 'STRESS' }
]

// 岗位选项
const positionOptions = computed(() => 
  positions.value.map(p => ({ label: p.position_name, value: p.id }))
)

// 软件选项
const softwareOptions = computed(() => 
  softwareList.value.map(s => ({ label: s.software_name, value: s.id }))
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
    loadScripts()
  },
  onUpdatePageSize: (pageSize: number) => {
    filters.page_size = pageSize
    loadScripts()
  }
})

const getScriptTypeLabel = (value: string | undefined) => {
  if (!value) return '-'
  const option = scriptTypeOptions.find(o => o.value === value)
  return option ? option.label : value
}

const getPositionName = (id: string | undefined) => {
  if (!id) return '-'
  const pos = positions.value.find(p => p.id === id)
  return pos ? pos.position_name : '-'
}

const getSoftwareName = (id: string | undefined) => {
  if (!id) return '-'
  const sw = softwareList.value.find(s => s.id === id)
  return sw ? sw.software_name : '-'
}

const columns = computed(() => [
  {
    title: '脚本名称',
    key: 'script_name',
    width: 200
  },
  {
    title: '脚本代码',
    key: 'script_code',
    width: 150
  },
  {
    title: '关联岗位',
    key: 'position_ids',
    width: 200,
    render: (row: Script) => {
      const posIds = row.position_ids || []
      if (!posIds.length) return '-'
      return h('div', { style: 'display: flex; flex-wrap: wrap; gap: 4px' }, 
        posIds.map((id: string) => {
          const pos = positions.value.find(p => p.id === id)
          return h(NTag, { size: 'small', type: 'info' }, { default: () => pos?.position_name || id })
        })
      )
    }
  },
  {
    title: '关联软件',
    key: 'software_id',
    width: 150,
    render: (row: Script) => getSoftwareName(row.software_id)
  },
  {
    title: '脚本类型',
    key: 'script_type',
    width: 120,
    render: (row: Script) => h(NTag, { size: 'small', type: 'info' }, 
      { default: () => getScriptTypeLabel(row.script_type) })
  },
  {
    title: '期望时长',
    key: 'expected_duration',
    width: 100,
    render: (row: Script) => `${row.expected_duration}秒`
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render: (row: Script) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, 
      { default: () => row.is_active ? '启用' : '禁用' })
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: Script) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, { default: () => '编辑' }),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          default: () => '确定删除?',
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' })
        })
      ]
    })
  }
])

const loadPositions = async () => {
  try {
    const res = await positionApi.list({ page_size: 100 })
    positions.value = res.data.items
  } catch (e) {
    console.error('加载岗位失败', e)
  }
}

const loadSoftware = async () => {
  try {
    const res = await softwareApi.list({ page_size: 100 })
    softwareList.value = res.data.items
  } catch (e) {
    console.error('加载软件失败', e)
  }
}

const loadScripts = async () => {
  loading.value = true
  try {
    const res = await scriptApi.list(filters)
    scripts.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (e: any) {
    message.error('加载脚本列表失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = null
  scriptForm.script_name = ''
  scriptForm.script_code = ''
  scriptForm.position_ids = []
  scriptForm.software_id = undefined
  scriptForm.script_type = ''
  scriptForm.script_content = ''
  scriptForm.expected_duration = 300
  showModal.value = true
}

const openEditModal = (row: Script) => {
  isEdit.value = true
  editingId.value = row.id
  scriptForm.script_name = row.script_name
  scriptForm.script_code = row.script_code
  scriptForm.position_ids = row.position_ids || []
  scriptForm.software_id = row.software_id
  scriptForm.script_type = row.script_type || ''
  scriptForm.script_content = row.script_content
  scriptForm.expected_duration = row.expected_duration
  showModal.value = true
}

const handleSave = async () => {
  if (!scriptForm.script_name || !scriptForm.script_code) {
    message.error('请填写必填项')
    return
  }
  
  saving.value = true
  try {
    if (isEdit.value && editingId.value) {
      await scriptApi.update(editingId.value, scriptForm)
      message.success('更新成功')
    } else {
      await scriptApi.create(scriptForm)
      message.success('创建成功')
    }
    showModal.value = false
    loadScripts()
  } catch (e: any) {
    message.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await scriptApi.delete(id)
    message.success('删除成功')
    loadScripts()
  } catch (e: any) {
    message.error('删除失败: ' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  loadPositions()
  loadSoftware()
  loadScripts()
})
</script>

<style scoped>
.script-list-page {
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

.filter-select {
  width: 160px;
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

.script-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.script-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.script-table :deep(.n-data-table-td) {
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
