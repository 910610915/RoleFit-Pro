<template>
  <div class="software-list-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <n-icon size="28" color="#0ea5e9"><CodeSlash /></n-icon>
          <n-h1 class="title">测试软件管理</n-h1>
        </div>
        <n-button type="primary" class="add-btn" @click="openAddModal">
          <template #icon><n-icon><Add /></n-icon></template>
          添加软件
        </n-button>
      </div>
    </div>
    
    <!-- Filters -->
    <n-card class="filter-card">
      <div class="filter-row">
        <n-select 
          v-model:value="filters.category" 
          placeholder="软件类别" 
          :options="categoryOptions" 
          clearable 
          class="category-select" 
        />
        <n-button type="primary" class="search-btn" @click="loadSoftware">
          <template #icon><n-icon><Search /></n-icon></template>
          搜索
        </n-button>
      </div>
    </n-card>
    
    <!-- Table -->
    <n-card class="table-card">
      <n-data-table
        :columns="columns"
        :data="softwareList"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: Software) => row.id"
        :bordered="false"
        class="software-table"
      />
    </n-card>
    
    <!-- Add/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑软件' : '添加新软件'" style="width: 700px; max-height: 80vh; overflow-y: auto" class="custom-modal">
      <n-form ref="formRef" :model="softwareForm" :rules="rules" label-placement="top">
        <!-- 基础信息 -->
        <n-divider title-placement="left">基础信息</n-divider>
        
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="软件名称" path="software_name">
              <n-input v-model:value="softwareForm.software_name" placeholder="如：PCMark 10" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="软件代码" path="software_code">
              <n-input v-model:value="softwareForm.software_code" placeholder="如：pcmark10" :disabled="isEdit" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="厂商" path="vendor">
              <n-input v-model:value="softwareForm.vendor" placeholder="如：UL Solutions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="类别" path="category">
              <n-select v-model:value="softwareForm.category" :options="categoryOptions" placeholder="选择类别" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="版本" path="version">
              <n-input v-model:value="softwareForm.version" placeholder="如：v1.0" />
            </n-form-item>
          </n-gi>
        </n-grid>
        
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="启动参数" path="launch_params">
              <n-input v-model:value="softwareForm.launch_params" placeholder="如：-game -windowed" />
            </n-form-item>
          </n-gi>
        </n-grid>
        
        <n-form-item label="描述" path="description">
          <n-input v-model:value="softwareForm.description" type="textarea" placeholder="软件描述..." :rows="2" />
        </n-form-item>
        
        <!-- 安装配置 -->
        <n-divider title-placement="left">安装配置</n-divider>
        
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="软件类型" path="software_type">
              <n-select v-model:value="softwareForm.software_type" :options="softwareTypeOptions" placeholder="选择类型" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="安装包格式" path="package_format">
              <n-select v-model:value="softwareForm.package_format" :options="packageFormatOptions" placeholder="选择格式" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="存储路径" path="storage_path">
              <n-input v-model:value="softwareForm.storage_path" placeholder="如：v1.0/ (相对于软件根目录)" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="目标安装目录" path="target_install_path">
              <n-input v-model:value="softwareForm.target_install_path" placeholder="如：C:\Program Files (x86)\BenchmarkTools" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="子文件夹" path="subfolder_name">
              <n-input v-model:value="softwareForm.subfolder_name" placeholder="如：pcmark10" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="主程序路径" path="main_exe_relative_path">
              <n-input v-model:value="softwareForm.main_exe_relative_path" placeholder="如：PCMark10.exe" />
            </n-form-item>
          </n-gi>
        </n-grid>
        
        <n-form-item label="静默安装命令" path="silent_install_cmd">
          <n-input v-model:value="softwareForm.silent_install_cmd" placeholder="如：/S /quiet 或 /qn" />
        </n-form-item>
        
        <!-- 检测配置 -->
        <n-divider title-placement="left">检测配置</n-divider>
        
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="检测方式" path="detection_method">
              <n-select v-model:value="softwareForm.detection_method" :options="detectionMethodOptions" placeholder="选择检测方式" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="检测关键字" path="detection_keyword">
              <n-input v-model:value="softwareForm.detection_keyword" placeholder="进程名或注册表路径" />
            </n-form-item>
          </n-gi>
        </n-grid>
        
        <n-form-item label="检测路径" path="detection_path">
          <n-input v-model:value="softwareForm.detection_path" placeholder="如：C:\Program Files (x86)\BenchmarkTools\pcmark10" />
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
  NCard, NH1, NButton, NSpace, NSelect, NDataTable, NModal, NForm, NFormItem, 
  NIcon, NTag, NPopconfirm, NGrid, NGi, NDivider, NInput
} from 'naive-ui'
import { Add, CodeSlash, Search } from '@vicons/ionicons5'
import { softwareApi, type Software } from '@/api/software'

const message = useMessage()

const softwareList = ref<Software[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)

const filters = reactive({
  page: 1,
  page_size: 20,
  category: undefined as string | undefined
})

const softwareForm = reactive({
  // 基础信息
  software_name: '',
  software_code: '',
  vendor: '',
  category: '',
  version: '',
  description: '',
  launch_params: '',
  // 安装配置
  software_type: 'portable' as 'installer' | 'portable' | undefined,
  package_format: undefined as 'exe' | 'msi' | 'zip' | 'rar' | '7z' | undefined,
  storage_path: '',
  target_install_path: '',
  subfolder_name: '',
  silent_install_cmd: '',
  main_exe_relative_path: '',
  // 检测配置
  detection_method: 'file' as 'file' | 'process' | 'registry' | undefined,
  detection_path: '',
  detection_keyword: ''
})

const rules = {
  software_name: { required: true, message: '请输入软件名称' },
  software_code: { required: true, message: '请输入软件代码' }
}

// 选项配置
const categoryOptions = [
  { label: '开发工具', value: 'DEV' },
  { label: '美术设计', value: 'ART' },
  { label: '动画制作', value: 'ANIM' },
  { label: '特效制作', value: 'VFX' },
  { label: 'UI设计', value: 'UI' },
  { label: '工具软件', value: 'TOOL' },
  { label: '办公软件', value: 'OFFICE' }
]

const softwareTypeOptions = [
  { label: '绿色版 (portable)', value: 'portable' },
  { label: '安装包 (installer)', value: 'installer' }
]

const packageFormatOptions = [
  { label: 'EXE 安装包', value: 'exe' },
  { label: 'MSI 安装包', value: 'msi' },
  { label: 'ZIP 压缩包', value: 'zip' },
  { label: 'RAR 压缩包', value: 'rar' },
  { label: '7-ZIP 压缩包', value: '7z' }
]

const detectionMethodOptions = [
  { label: '文件/目录检测', value: 'file' },
  { label: '进程检测', value: 'process' },
  { label: '注册表检测', value: 'registry' }
]

const getSoftwareTypeLabel = (value: string | undefined) => {
  if (!value) return '-'
  const option = softwareTypeOptions.find(o => o.value === value)
  return option ? option.label : value
}

const columns = computed(() => [
  {
    title: '软件名称',
    key: 'software_name',
    width: 180
  },
  {
    title: '代码',
    key: 'software_code',
    width: 100
  },
  {
    title: '版本',
    key: 'version',
    width: 80
  },
  {
    title: '类型',
    key: 'software_type',
    width: 100,
    render: (row: Software) => h(NTag, { size: 'small', type: row.software_type === 'portable' ? 'success' : 'info' }, 
      { default: () => getSoftwareTypeLabel(row.software_type) })
  },
  {
    title: '格式',
    key: 'package_format',
    width: 80
  },
  {
    title: '检测方式',
    key: 'detection_method',
    width: 100,
    render: (row: Software) => row.detection_method || '-'
  },
  {
    title: '目标目录',
    key: 'target_install_path',
    ellipsis: { tooltip: true },
    width: 200
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row: Software) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, 
      { default: () => row.is_active ? '启用' : '禁用' })
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: Software) => h(NSpace, { size: 'small' }, {
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

const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  itemCount: 0,
  onChange: (page: number) => {
    filters.page = page
    loadSoftware()
  },
  onUpdatePageSize: (pageSize: number) => {
    filters.page_size = pageSize
    loadSoftware()
  }
})

const loadSoftware = async () => {
  loading.value = true
  try {
    const res = await softwareApi.list(filters)
    softwareList.value = res.data.items
    pagination.value.itemCount = res.data.total
  } catch (e: any) {
    message.error('加载软件列表失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  softwareForm.software_name = ''
  softwareForm.software_code = ''
  softwareForm.vendor = ''
  softwareForm.category = ''
  softwareForm.version = ''
  softwareForm.description = ''
  softwareForm.launch_params = ''
  softwareForm.software_type = 'portable'
  softwareForm.package_format = undefined
  softwareForm.storage_path = ''
  softwareForm.target_install_path = ''
  softwareForm.subfolder_name = ''
  softwareForm.silent_install_cmd = ''
  softwareForm.main_exe_relative_path = ''
  softwareForm.detection_method = 'file'
  softwareForm.detection_path = ''
  softwareForm.detection_keyword = ''
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  showModal.value = true
}

const openEditModal = (row: Software) => {
  isEdit.value = true
  editingId.value = row.id
  
  softwareForm.software_name = row.software_name || ''
  softwareForm.software_code = row.software_code || ''
  softwareForm.vendor = row.vendor || ''
  softwareForm.category = row.category || ''
  softwareForm.version = row.version || ''
  softwareForm.description = row.description || ''
  softwareForm.launch_params = row.launch_params || ''
  softwareForm.software_type = row.software_type || 'portable'
  softwareForm.package_format = row.package_format
  softwareForm.storage_path = row.storage_path || ''
  softwareForm.target_install_path = row.target_install_path || ''
  softwareForm.subfolder_name = row.subfolder_name || ''
  softwareForm.silent_install_cmd = row.silent_install_cmd || ''
  softwareForm.main_exe_relative_path = row.main_exe_relative_path || ''
  softwareForm.detection_method = row.detection_method || 'file'
  softwareForm.detection_path = row.detection_path || ''
  softwareForm.detection_keyword = row.detection_keyword || ''
  
  showModal.value = true
}

const handleSave = async () => {
  if (!softwareForm.software_name || !softwareForm.software_code) {
    message.error('请填写必填项')
    return
  }
  
  saving.value = true
  try {
    if (isEdit.value && editingId.value) {
      await softwareApi.update(editingId.value, softwareForm)
      message.success('更新成功')
    } else {
      await softwareApi.create(softwareForm)
      message.success('创建成功')
    }
    showModal.value = false
    loadSoftware()
  } catch (e: any) {
    message.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await softwareApi.delete(id)
    message.success('删除成功')
    loadSoftware()
  } catch (e: any) {
    message.error('删除失败: ' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  loadSoftware()
})
</script>

<style scoped>
.software-list-page {
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

.category-select {
  width: 160px;
  border-radius: 8px;
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

.software-table :deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #475569;
}

.software-table :deep(.n-data-table-tr:hover) {
  background: rgba(14, 165, 233, 0.04);
}

.software-table :deep(.n-data-table-td) {
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
