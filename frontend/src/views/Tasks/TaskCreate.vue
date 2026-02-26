<template>
  <div class="task-create">
    <n-button @click="router.back()" class="back-btn">
      <template #icon><n-icon><arrow-back /></n-icon></template>
      返回
    </n-button>
    
    <n-card title="创建测试任务">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left">
        <n-form-item label="任务名称" path="task_name">
          <n-input v-model:value="form.task_name" />
        </n-form-item>
        
        <n-form-item label="任务类型" path="task_type">
          <n-select v-model:value="form.task_type" :options="taskTypeOptions.map(t => ({label: t.label, value: t.value}))" />
        </n-form-item>
        
        <!-- 测试类型说明 -->
        <n-card v-if="form.task_type" class="test-type-info" size="small">
          <n-space vertical>
            <n-space align="center">
              <n-tag type="info">{{ getTestTypeInfo(form.task_type)?.label }}</n-tag>
              <span class="duration">预计时长: {{ getTestTypeInfo(form.task_type)?.duration }}</span>
            </n-space>
            <n-text depth="3">{{ getTestTypeInfo(form.task_type)?.description }}</n-text>
            <n-space>
              <n-text depth="2">测试项目:</n-text>
              <n-tag v-for="item in getTestTypeInfo(form.task_type)?.items" :key="item" size="small" type="success">{{ item }}</n-tag>
            </n-space>
          </n-space>
        </n-card>
        
        <n-form-item label="目标设备">
          <n-select
            v-model:value="form.target_device_ids"
            multiple
            filterable
            placeholder="选择设备"
            :options="deviceOptions"
          />
        </n-form-item>
        
        <n-form-item label="调度类型">
          <n-radio-group v-model:value="form.schedule_type">
            <n-space>
              <n-radio value="immediate">立即执行</n-radio>
              <n-radio value="scheduled">定时执行</n-radio>
              <n-radio value="recurring">循环执行</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>
        
        <n-form-item v-if="form.schedule_type === 'scheduled'" label="计划时间">
          <n-date-picker v-model:formatted-value="form.scheduled_at" type="datetime" />
        </n-form-item>
        
        <n-form-item label="测试时长(秒)">
          <n-input-number v-model:value="form.test_duration_seconds" :min="60" :max="86400" />
        </n-form-item>
        
        <n-form-item>
          <n-space>
            <n-button type="primary" @click="handleSubmit" :loading="saving">创建</n-button>
            <n-button @click="router.back()">取消</n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NButton, NForm, NFormItem, NInput, NSelect, NRadioGroup, NRadio, NSpace, NDatePicker, NInputNumber, NIcon, NText, NTag } from 'naive-ui'
import { ArrowBack } from '@vicons/ionicons5'
import { taskApi, type TaskCreate } from '@/api/tasks'
import { deviceApi, type Device } from '@/api/devices'

const router = useRouter()

const formRef = ref()
const saving = ref(false)

const form = reactive<TaskCreate>({
  task_name: '',
  task_type: 'benchmark',
  target_device_ids: [],
  schedule_type: 'immediate',
  test_duration_seconds: 3600
})

const rules = {
  task_name: { required: true, message: '请输入任务名称' },
  task_type: { required: true, message: '请选择任务类型' }
}

const taskTypeOptions = [
  { 
    label: '性能测试', 
    value: 'benchmark',
    description: '快速测试CPU、GPU、内存、磁盘的基础性能，适合日常巡检',
    duration: '约5-10分钟',
    items: ['CPU跑分', 'GPU跑分', '内存读写', '磁盘读写']
  },
  { 
    label: '模拟测试', 
    value: 'simulation',
    description: '模拟游戏工作负载，测试设备在游戏开发场景下的表现',
    duration: '约15-20分钟',
    items: ['CPU多核渲染', 'GPU图形渲染', '内存压力', '磁盘IO']
  },
  { 
    label: '完整测试', 
    value: 'full',
    description: '全面的硬件性能测试，包含所有测试项目，生成详细报告',
    duration: '约30-60分钟',
    items: ['CPU基准测试', 'GPU基准测试', '内存压力测试', '磁盘基准测试', '综合评分']
  },
  { 
    label: '自定义', 
    value: 'custom',
    description: '自定义测试项目，灵活选择需要测试的硬件组件',
    duration: '根据选择项目',
    items: ['可选择CPU/GPU/内存/磁盘', '可设置测试时长', '可设置采样间隔']
  }
]

// 获取测试类型的详细说明
const getTestTypeInfo = (type: string) => {
  return taskTypeOptions.find(t => t.value === type)
}

const deviceOptions = ref<{ label: string; value: string }[]>([])

const loadDevices = async () => {
  try {
    const res = await deviceApi.list({ page_size: 100 })
    deviceOptions.value = res.data.items.map(d => ({
      label: `${d.device_name} (${d.ip_address})`,
      value: d.id
    }))
  } catch (error) {
    console.error('Failed to load devices:', error)
  }
}

const handleSubmit = async () => {
  try {
    saving.value = true
    await taskApi.create(form)
    router.push('/tasks')
  } catch (error) {
    console.error('Failed to create task:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.task-create {
  padding: 20px;
  max-width: 800px;
}

.back-btn {
  margin-bottom: 20px;
}

.test-type-info {
  margin-bottom: 20px;
  background-color: #f0f2f5;
}

.duration {
  font-size: 12px;
  color: #666;
}
</style>
