<template>
  <div class="position-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><Business /></n-icon>
          <n-h1 class="title">岗位管理</n-h1>
        </div>
        <n-button type="primary" class="add-btn" @click="openAddModal">
          <template #icon><n-icon><Add /></n-icon></template>
          添加岗位
        </n-button>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-input 
          v-model:value="filters.keyword" 
          placeholder="搜索岗位名称..." 
          clearable 
          class="search-input" 
        />
        <n-select 
          v-model:value="filters.department" 
          placeholder="所属部门" 
          :options="deptOptions" 
          clearable 
          class="dept-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadPositions">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="positions"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Position) => row.id"
        :bordered="false"
        class="position-table"
      />
    </n-card>
    
    <!-- Add/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑岗位' : '添加新岗位'" style="width: 600px" class="custom-modal">
      <n-form ref="formRef" :model="positionForm" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="岗位名称" path="position_name">
          <n-input v-model:value="positionForm.position_name" placeholder="如：UE4开发工程师" />
        </n-form-item>
        <n-form-item label="岗位代码" path="position_code">
          <n-input v-model:value="positionForm.position_code" placeholder="如：UE4_DEV" :disabled="isEdit" />
        </n-form-item>
        <n-form-item label="所属部门" path="department">
          <n-select v-model:value="positionForm.department" :options="deptOptions" placeholder="选择部门" clearable />
        </n-form-item>
        <n-form-item label="岗位描述" path="description">
          <n-input v-model:value="positionForm.description" type="textarea" placeholder="岗位描述和职责" />
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
  NCard, NH1, NButton, NSpace, NInput, NSelect, NDataTable, NModal, NForm, NFormItem, NIcon, NTag, NPopconfirm 
} from 'naive-ui'
import { Add, Trash, Pencil, Business, Search } from '@vicons/ionicons5'
import { positionApi, type Position } from '@/api/positions'

const message = useMessage()

const positions = ref<Position[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)

const filters = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  department: undefined as string | undefined
})

const positionForm = reactive({
  position_name: '',
  position_code: '',
  department: '',
  description: ''
})

const rules = {
  position_name: { required: true, message: '请输入岗位名称' },
  position_code: { required: true, message: '请输入岗位代码' }
}

// 部门选项
const deptOptions = [
  { label: '技术开发部', value: '技术开发部' },
  { label: '美术设计部', value: '美术设计部' },
  { label: '动画制作部', value: '动画制作部' },
  { label: '特效制作部', value: '特效制作部' },
  { label: 'UI设计部', value: 'UI设计部' },
  { label: '测试 QA', value: '测试QA' },
  { label: '运维部', value: '运维部' },
  { label: '产品部', value: '产品部' },
  { label: '项目管理', value: '项目管理' }
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  itemCount: 0,
  onChange: (page: number) => {
    filters.page = page
    loadPositions()
  },
  onUpdatePageSize: (pageSize: number) => {
    filters.page_size = pageSize
    loadPositions()
  }
})

const columns = computed(() => [
  {
    title: '岗位名称',
    key: 'position_name',
    width: 200
  },
  {
    title: '岗位代码',
    key: 'position_code',
    width: 150
  },
  {
    title: '部门',
    key: 'department',
    width: 150
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: { tooltip: true }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render: (row: Position) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, 
      { default: () => row.is_active ? '启用' : '禁用' })
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row: Position) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: Position) => h(NSpace, { size: 'small' }, {
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
  loading.value = true
  try {
    const res = await positionApi.list(filters)
    positions.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (e: any) {
    message.error('加载岗位列表失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = null
  positionForm.position_name = ''
  positionForm.position_code = ''
  positionForm.department = ''
  positionForm.description = ''
  showModal.value = true
}

const openEditModal = (row: Position) => {
  isEdit.value = true
  editingId.value = row.id
  positionForm.position_name = row.position_name
  positionForm.position_code = row.position_code
  positionForm.department = row.department || ''
  positionForm.description = row.description || ''
  showModal.value = true
}

const handleSave = async () => {
  if (!positionForm.position_name || !positionForm.position_code) {
    message.error('请填写必填项')
    return
  }
  
  saving.value = true
  try {
    if (isEdit.value && editingId.value) {
      await positionApi.update(editingId.value, positionForm)
      message.success('更新成功')
    } else {
      await positionApi.create(positionForm)
      message.success('创建成功')
    }
    showModal.value = false
    loadPositions()
  } catch (e: any) {
    message.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await positionApi.delete(id)
    message.success('删除成功')
    loadPositions()
  } catch (e: any) {
    message.error('删除失败: ' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  loadPositions()
})
</script>

<style scoped>
.position-list-page {
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

.search-input {
  flex: 1;
  max-width: 280px;
}

.dept-select {
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

.position-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.position-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.position-table :deep(.n-data-table-td) {
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
