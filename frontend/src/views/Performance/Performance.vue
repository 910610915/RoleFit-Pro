<template>
  <div class="performance-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">性能监控</h1>
        <span class="page-subtitle">实时硬件性能监控与AI分析</span>
      </div>
      <div class="header-right">
        <n-select
          v-model:value="selectedDevice"
          :options="deviceOptions"
          placeholder="选择设备"
          style="width: 200px"
          @update:value="onDeviceChange"
        />
        <n-button type="primary" @click="refreshData">
          <template #icon>
<n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </header>

    <!-- Device Hardware Info -->
    <section class="device-info-section" v-if="currentDeviceInfo">
      <n-card title="设备硬件信息" size="small">
        <n-tabs type="line" size="small">
          <n-tab-pane name="info" tab="基本信息">
            <n-descriptions :column="3" label-placement="left" bordered>
              <n-descriptions-item label="设备名称">{{ currentDeviceInfo.device_name || '-' }}</n-descriptions-item>
              <n-descriptions-item label="IP地址">{{ currentDeviceInfo.ip_address || '-' }}</n-descriptions-item>
              <n-descriptions-item label="主机名">{{ currentDeviceInfo.hostname || '-' }}</n-descriptions-item>
              <n-descriptions-item label="MAC地址">{{ currentDeviceInfo.mac_address || '-' }}</n-descriptions-item>
              <n-descriptions-item label="部门">{{ currentDeviceInfo.department || '-' }}</n-descriptions-item>
              <n-descriptions-item label="岗位">{{ currentDeviceInfo.position || '-' }}</n-descriptions-item>
              <n-descriptions-item label="操作系统">{{ currentDeviceInfo.os_name || '-' }} {{ currentDeviceInfo.os_version || '' }}</n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag :type="currentDeviceInfo.status === 'online' ? 'success' : 'default'" size="small">
                  {{ currentDeviceInfo.status === 'online' ? '在线' : currentDeviceInfo.status === 'offline' ? '离线' : currentDeviceInfo.status }}
                </n-tag>
              </n-descriptions-item>
            </n-descriptions>
          </n-tab-pane>
          <n-tab-pane name="cpu" tab="CPU">
            <n-descriptions :column="2" label-placement="left" bordered>
              <n-descriptions-item label="型号">{{ currentDeviceInfo.cpu_model || '-' }}</n-descriptions-item>
              <n-descriptions-item label="核心数">{{ currentDeviceInfo.cpu_cores || '-' }}</n-descriptions-item>
              <n-descriptions-item label="线程数">{{ currentDeviceInfo.cpu_threads || '-' }}</n-descriptions-item>
              <n-descriptions-item label="基础频率">{{ currentDeviceInfo.cpu_base_clock ? currentDeviceInfo.cpu_base_clock + ' GHz' : '-' }}</n-descriptions-item>
            </n-descriptions>
          </n-tab-pane>
          <n-tab-pane name="gpu" tab="GPU">
            <n-descriptions :column="2" label-placement="left" bordered>
              <n-descriptions-item label="型号">{{ currentDeviceInfo.gpu_model || '-' }}</n-descriptions-item>
              <n-descriptions-item label="显存">{{ currentDeviceInfo.gpu_vram_mb ? currentDeviceInfo.gpu_vram_mb + ' MB' : '-' }}</n-descriptions-item>
              <n-descriptions-item label="驱动版本">{{ currentDeviceInfo.gpu_driver_version || '-' }}</n-descriptions-item>
            </n-descriptions>
          </n-tab-pane>
          <n-tab-pane name="memory" tab="内存">
            <n-descriptions :column="2" label-placement="left" bordered>
              <n-descriptions-item label="总容量">{{ currentDeviceInfo.ram_total_gb ? currentDeviceInfo.ram_total_gb + ' GB' : '-' }}</n-descriptions-item>
              <n-descriptions-item label="频率">{{ currentDeviceInfo.ram_frequency ? currentDeviceInfo.ram_frequency + ' MHz' : '-' }}</n-descriptions-item>
            </n-descriptions>
          </n-tab-pane>
          <n-tab-pane name="storage" tab="存储">
            <n-space vertical>
              <!-- 显示全量磁盘 -->
              <n-card v-if="currentDeviceInfo.all_disks && currentDeviceInfo.all_disks.length > 0" size="small" title="磁盘列表">
                <n-descriptions v-for="(disk, index) in currentDeviceInfo.all_disks" :key="index" :column="2" label-placement="left" bordered>
                  <n-descriptions-item :label="'磁盘 ' + (index + 1)">{{ disk.model || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="容量">{{ disk.capacity_tb ? disk.capacity_tb + ' TB' : disk.capacity_gb ? (disk.capacity_gb / 1024).toFixed(1) + ' TB' : '-' }}</n-descriptions-item>
                  <n-descriptions-item label="类型">{{ disk.type || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="接口">{{ disk.interface || '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-card>
              <!-- 备用显示单个磁盘 -->
              <n-descriptions v-else :column="2" label-placement="left" bordered>
                <n-descriptions-item label="型号">{{ currentDeviceInfo.disk_model || '-' }}</n-descriptions-item>
                <n-descriptions-item label="容量">{{ currentDeviceInfo.disk_capacity_tb ? currentDeviceInfo.disk_capacity_tb + ' TB' : '-' }}</n-descriptions-item>
                <n-descriptions-item label="类型">{{ currentDeviceInfo.disk_type || '-' }}</n-descriptions-item>
              </n-descriptions>
            </n-space>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </section>

    <!-- Real-time Metrics Cards -->
    <section class="metrics-section">
      <div class="metric-card" v-for="metric in currentMetrics" :key="metric.key">
        <div class="metric-header">
          <div class="metric-icon" :style="{ backgroundColor: metric.color + '20', color: metric.color }">
            <n-icon size="24"><component :is="metric.icon" /></n-icon>
          </div>
          <div class="metric-title">{{ metric.label }}</div>
        </div>
        <div class="metric-value">
          <span class="value">{{ metric.value }}</span>
          <span class="unit">{{ metric.unit }}</span>
        </div>
        <div class="metric-progress">
          <n-progress
            type="line"
            :percentage="metric.percentage"
            :color="metric.color"
            :rail-color="metric.color + '30'"
            :height="8"
          />
        </div>
        <div class="metric-details">
          <span>峰值: {{ metric.peak }}</span>
          <span>平均: {{ metric.avg }}</span>
        </div>
      </div>
    </section>

    <!-- Charts Row -->
    <section class="charts-section">
      <div class="chart-card">
        <div class="chart-header">
          <h3>CPU 使用率趋势</h3>
          <n-radio-group v-model:value="cpuTimeRange" size="small" @update:value="refreshCpuChart">
            <n-radio-button value="1m">1分钟</n-radio-button>
            <n-radio-button value="5m">5分钟</n-radio-button>
            <n-radio-button value="15m">15分钟</n-radio-button>
          </n-radio-group>
        </div>
        <div ref="cpuChartRef" style="height: 250px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>GPU 使用率趋势</h3>
          <div style="display: flex; gap: 8px;">
            <n-radio-group v-model:value="gpuMetricType" size="small" @update:value="refreshGpuChart">
              <n-radio-button value="usage">使用率</n-radio-button>
              <n-radio-button value="memory">显存</n-radio-button>
            </n-radio-group>
            <n-radio-group v-model:value="gpuTimeRange" size="small" @update:value="refreshGpuChart">
              <n-radio-button value="1m">1分钟</n-radio-button>
              <n-radio-button value="5m">5分钟</n-radio-button>
              <n-radio-button value="15m">15分钟</n-radio-button>
            </n-radio-group>
          </div>
        </div>
        <div ref="gpuChartRef" style="height: 250px;"></div>
      </div>
    </section>

    <!-- Memory and Disk IO Charts -->
    <section class="charts-section">
      <div class="chart-card">
        <div class="chart-header">
          <h3>内存 使用率趋势</h3>
          <n-radio-group v-model:value="memoryTimeRange" size="small" @update:value="refreshMemoryChart">
            <n-radio-button value="1m">1分钟</n-radio-button>
            <n-radio-button value="5m">5分钟</n-radio-button>
            <n-radio-button value="15m">15分钟</n-radio-button>
          </n-radio-group>
        </div>
        <div ref="memoryChartRef" style="height: 250px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <h3>磁盘IO 趋势</h3>
            <n-select 
              v-model:value="selectedDisk" 
              :options="diskOptions" 
              size="small" 
              style="width: 120px"
              @update:value="refreshDiskChart"
            />
          </div>
          <div style="display: flex; gap: 8px;">
            <n-radio-group v-model:value="diskMetricType" size="small" @update:value="refreshDiskChart">
              <n-radio-button value="throughput">吞吐量</n-radio-button>
              <n-radio-button value="iops">IOPS/队列</n-radio-button>
              <n-radio-button value="latency">延迟</n-radio-button>
            </n-radio-group>
          </div>
        </div>
        <div ref="diskIOChartRef" style="height: 250px;"></div>
      </div>
    </section>

    <!-- Process Monitor -->
    <section class="process-section">
      <div class="section-header">
        <h3>进程资源消耗排行 (Top 10)</h3>
        <n-button size="small" @click="loadProcesses" :loading="processLoading">
          <template #icon><n-icon><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
      </div>
      <n-data-table
        v-if="processes.length > 0"
        :columns="processColumns"
        :data="processes"
        :loading="processLoading"
        :pagination="false"
        :max-height="300"
        size="medium"
      />
      <n-empty v-else description="暂无进程数据，请确保Agent已启动并正在监控" />
    </section>

    <!-- 自定义看板 - 暂时注释，与主图表重复
    <section class="widget-board" v-if="userRole === 'admin' || userRole === 'manager'">
      <div class="widget-header">
        <h3>自定义看板</h3>
        <n-button size="small" @click="showWidgetConfig = true">
          <template #icon><n-icon><SettingsOutline /></n-icon></template>
          配置
        </n-button>
      </div>
      <div class="widget-grid">
        <div v-for="widget in activeWidgets" :key="widget.id" class="widget-card">
          <h4>{{ widget.title }}</h4>
          <component :is="widget.component" :data="widget.data" :vram-data="widget.vramData" />
        </div>
      </div>
    </section>
    -->

    <!-- Bottom Row -->
    <section class="bottom-section">
      <!-- Benchmarks -->
      <div class="benchmarks-card">
        <div class="card-header">
          <h3>基准测试结果</h3>
          <n-button size="small" @click="showBenchmarkModal = true">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            新建测试
          </n-button>
        </div>
        <n-data-table
          :columns="benchmarkColumns"
          :data="benchmarks"
          :loading="benchmarkLoading"
          :pagination="false"
          :max-height="300"
        />
      </div>

      <!-- AI Analysis -->
      <div class="analysis-card">
        <div class="card-header">
          <h3>AI 智能分析</h3>
          <n-button size="small" type="primary" @click="runAIAnalysis" :loading="aiLoading">
            <template #icon><n-icon><Bulb /></n-icon></template>
            一键分析
          </n-button>
        </div>
        <div class="analysis-content">
          <n-spin :show="aiLoading">
            <div v-if="aiAnalysis" class="analysis-result">
              <n-alert type="info" :title="aiAnalysis.title">
                {{ aiAnalysis.summary }}
              </n-alert>
              <div v-if="aiAnalysis.recommendations" class="recommendations">
                <h4>建议</h4>
                <p>{{ aiAnalysis.recommendations }}</p>
              </div>
            </div>
            <div v-else class="analysis-empty">
              <n-empty description="点击一键分析生成报告">
              </n-empty>
            </div>
          </n-spin>
        </div>
      </div>
    </section>

    <!-- Alerts -->
    <section class="alerts-section">
      <div class="card-header">
        <h3>性能告警</h3>
        <n-badge :value="alerts.length" :max="99">
          <n-icon size="20"><Alert /></n-icon>
        </n-badge>
      </div>
      <div class="alerts-list">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          class="alert-item"
          :class="alert.severity"
        >
          <div class="alert-icon">
            <n-icon size="20"><Warning /></n-icon>
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
          </div>
          <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
        </div>
        <n-empty v-if="!alerts.length" description="暂无告警" />
      </div>
    </section>

    <!-- Widget Config Modal -->
    <WidgetConfigModal
      v-model:show="showWidgetConfig"
      :active="activeWidgets.map(w => w.id)"
      @save="updateWidgets"
    />

    <!-- Benchmark Modal -->
    <n-modal v-model:show="showBenchmarkModal" preset="card" title="新建基准测试" style="width: 500px;">
      <n-form ref="benchmarkFormRef" :model="benchmarkForm" :rules="benchmarkRules">
        <n-form-item label="测试软件" path="software_code">
          <n-select v-model:value="benchmarkForm.software_code" :options="softwareOptions" />
        </n-form-item>
        <n-form-item label="测试类型" path="benchmark_type">
          <n-select v-model:value="benchmarkForm.benchmark_type" :options="benchmarkTypeOptions" />
        </n-form-item>
        <n-form-item label="测试场景" path="test_scene">
          <n-input v-model:value="benchmarkForm.test_scene" placeholder="可选：场景名称或项目路径" />
        </n-form-item>
        
        <!-- Granular Control -->
        <n-divider title-placement="left">精细化控制</n-divider>
        <n-form-item label="启用闲置检测 (前置检查)" path="pre_flight_check">
          <n-switch v-model:value="benchmarkForm.pre_flight_check" />
          <span style="margin-left: 8px; font-size: 12px; color: #666;">仅在鼠标键盘无操作5分钟后启动</span>
        </n-form-item>
        <div style="display: flex; gap: 16px;">
          <n-form-item label="CPU 资源限制 (%)" path="resource_limit_cpu" style="flex: 1">
            <n-input-number v-model:value="benchmarkForm.resource_limit_cpu" :min="10" :max="100" />
          </n-form-item>
          <n-form-item label="内存 资源限制 (%)" path="resource_limit_mem" style="flex: 1">
            <n-input-number v-model:value="benchmarkForm.resource_limit_mem" :min="10" :max="100" />
          </n-form-item>
        </div>
      </n-form>
      <template #footer>
        <n-button @click="showBenchmarkModal = false">取消</n-button>
        <n-button type="primary" @click="startBenchmark" :loading="startingBenchmark">开始测试</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, h } from 'vue'
import * as echarts from 'echarts'
import { 
  NCard, NButton, NSelect, NIcon, NDataTable, NModal, NForm, 
  NFormItem, NInput, NInputNumber, NRadioGroup, NRadioButton,
  NProgress, useMessage, NEmpty, NSpace, NTag, NAvatar,
  NDescriptions, NDescriptionsItem, NGrid, NGi, NStatistic,
  NTabs, NTabPane
} from 'naive-ui'
import {
  HardwareChip, SpeedometerOutline, ServerOutline, RefreshOutline,
  SettingsOutline, AddOutline, DesktopOutline, WarningOutline, TrendingUpOutline, 
  CloudUploadOutline, Construct, Grid
} from '@vicons/ionicons5'
import api from '@/api'
import WidgetConfigModal from '@/components/WidgetConfigModal.vue'
import CpuWidget from '@/components/widgets/CpuWidget.vue'
import GpuWidget from '@/components/widgets/GpuWidget.vue'
import AlertsWidget from '@/components/widgets/AlertsWidget.vue'

// Icons
const iconMap: Record<string, any> = {
  cpu: Construct,
  gpu: HardwareChip,
  memory: SpeedometerOutline,
  disk: ServerOutline,
  default: Grid
}

// State
const selectedDevice = ref<string | null>(null)
const deviceOptions = ref<{label: string, value: string}[]>([])
const currentMetrics = ref<any[]>([])
const cpuTimeRange = ref('5m')
const gpuTimeRange = ref('5m')
const gpuMetricType = ref('usage')
const memoryTimeRange = ref('5m')
const diskTimeRange = ref('5m')
const diskMetricType = ref('throughput')
const selectedDisk = ref('all')
const diskOptions = ref([{ label: '所有磁盘', value: 'all' }])

const cpuChartRef = ref<HTMLElement | null>(null)
const gpuChartRef = ref<HTMLElement | null>(null)
const memoryChartRef = ref<HTMLElement | null>(null)
const diskIOChartRef = ref<HTMLElement | null>(null)
let cpuChart: echarts.ECharts | null = null
let gpuChart: echarts.ECharts | null = null
let memoryChart: echarts.ECharts | null = null
let diskIOChart: echarts.ECharts | null = null
const gpuVramHistory = ref<number[]>([])

// Device info for hardware display
const currentDeviceInfo = ref<any>(null)

// Benchmarks
const benchmarks = ref<any[]>([])
const benchmarkLoading = ref(false)
const showBenchmarkModal = ref(false)

// Process monitoring
const processes = ref<any[]>([])
const processLoading = ref(false)

const processColumns = [
  { title: '进程名', key: 'name', width: 200 },
  { title: 'PID', key: 'pid', width: 80 },
  { title: 'CPU %', key: 'cpu', width: 80,
    render: (row: any) => `${(row.cpu || 0).toFixed(1)}%`
  },
  { title: '内存 %', key: 'memory', width: 80,
    render: (row: any) => `${(row.memory || 0).toFixed(1)}%`
  },
  { title: '路径', key: 'path', ellipsis: { tooltip: true } }
]

const loadProcesses = async () => {
  if (!selectedDevice.value) return
  
  processLoading.value = true
  try {
    const { data } = await api.get(`/performance/metrics/latest?device_id=${selectedDevice.value}`)
    
    if (data.top_processes && Array.isArray(data.top_processes)) {
      // Process list - Top 10 by CPU usage
      processes.value = data.top_processes
        .sort((a: any, b: any) => b.cpu - a.cpu)
        .slice(0, 10)
        .map((p: any) => ({
          name: p.name,
          pid: p.pid,
          cpu: Number((p.cpu || 0).toFixed(1)),
          memory: Number((p.memory || 0).toFixed(1)),
          path: p.path || ''
        }))
    }
  } catch (e) {
    console.error('Failed to load processes:', e)
  } finally {
    processLoading.value = false
  }
}

const showWidgetConfig = ref(false)
const userRole = ref('admin') // Should fetch from user store
const message = useMessage()
const activeWidgets = ref<any[]>([])
const widgetMap: Record<string, any> = {
  cpu: { component: CpuWidget, title: 'CPU 趋势图' },
  gpu: { component: GpuWidget, title: 'GPU 趋势图' },
  alerts: { component: AlertsWidget, title: '活跃告警' }
}

const updateWidgets = (keys: string[]) => {
  activeWidgets.value = keys.map(key => {
    const config = widgetMap[key]
    if (!config) return null
    
    let data = null
    if (key === 'cpu') {
      data = (cpuChart?.getOption() as any)?.series?.[0]?.data || []
    } else if (key === 'gpu') {
      data = (gpuChart?.getOption() as any)?.series?.[0]?.data || []
    } else if (key === 'alerts') {
      data = alerts.value
    }
    
    return {
      id: key,
      component: config.component,
      title: config.title,
      data: data,
      vramData: key === 'gpu' ? gpuVramHistory.value : undefined
    }
  }).filter(Boolean)
  
  // Save to local storage
  localStorage.setItem('rolefit_dashboard_widgets', JSON.stringify(keys))
}

const loadSavedWidgets = () => {
  try {
    const saved = localStorage.getItem('rolefit_dashboard_widgets')
    if (saved) {
      updateWidgets(JSON.parse(saved))
    } else {
      // Default widgets
      updateWidgets(['cpu', 'alerts'])
    }
  } catch (e) {
    console.error('Failed to load widgets:', e)
  }
}

// Watch data changes to update widget data
const refreshWidgetData = () => {
  activeWidgets.value.forEach(widget => {
    if (widget.id === 'cpu') {
      widget.data = (cpuChart?.getOption() as any)?.series?.[0]?.data || []
    } else if (widget.id === 'gpu') {
      widget.data = (gpuChart?.getOption() as any)?.series?.[0]?.data || []
      widget.vramData = gpuVramHistory.value
    } else if (widget.id === 'alerts') {
      widget.data = alerts.value
    }
  })
}

const startingBenchmark = ref(false)
const benchmarkFormRef = ref(null)
const benchmarkForm = reactive({
  software_code: null,
  benchmark_type: null,
  test_scene: '',
  pre_flight_check: true,
  resource_limit_cpu: 80,
  resource_limit_mem: 80
})
const benchmarkRules = {
  software_code: { required: true, message: '请选择测试软件' },
  benchmark_type: { required: true, message: '请选择测试类型' }
}
const softwareOptions = [
  { label: 'Blender', value: 'blender' },
  { label: 'Unreal Engine', value: 'unreal' },
  { label: 'Maya', value: 'maya' },
  { label: 'Photoshop', value: 'photoshop' },
]
const benchmarkTypeOptions = [
  { label: '渲染测试', value: 'render' },
  { label: '视口测试', value: 'viewport' },
  { label: '启动测试', value: 'launch' },
  { label: '编译测试', value: 'compile' },
]

const aiLoading = ref(false)
const aiAnalysis = ref<any>(null)
const alerts = ref<any[]>([])

// Metric cards configuration
const metricConfig = [
  { key: 'cpu', label: 'CPU', icon: iconMap.cpu, color: '#3b82f6', unit: '%' },
  { key: 'gpu', label: 'GPU', icon: iconMap.gpu, color: '#8b5cf6', unit: '%' },
  { key: 'memory', label: '内存', icon: iconMap.memory, color: '#10b981', unit: '%' },
  { key: 'disk', label: '磁盘IO', icon: iconMap.disk, color: '#f59e0b', unit: 'MB/s' },
]

const benchmarkColumns = [
  { title: '软件', key: 'software_code', width: 100 },
  { title: '类型', key: 'benchmark_type', width: 80 },
  { title: '得分', key: 'score', width: 80 },
  { title: 'CPU', key: 'score_cpu', width: 60 },
  { title: 'GPU', key: 'score_gpu', width: 60 },
  { title: '状态', key: 'status', width: 80,
    render: (row: any) => {
      const statusMap: Record<string, string> = {
        success: '成功', failed: '失败', running: '运行中'
      }
      return statusMap[row.status] || row.status
    }
  },
  { title: '时间', key: 'created_at', width: 150,
    render: (row: any) => formatTime(row.created_at)
  },
]

// Methods
const loadDevices = async () => {
  try {
    const { data } = await api.get('/devices')
    console.log('Devices loaded:', data)
    
    if (data.items && data.items.length > 0) {
      deviceOptions.value = data.items.map((d: any) => ({
        label: d.device_name,
        value: d.id,
        ...d
      }))
      if (!selectedDevice.value) {
        selectedDevice.value = deviceOptions.value[0].value
        // Store full device info
        currentDeviceInfo.value = deviceOptions.value[0]
      }
    } else {
      console.warn('No devices found')
      message.warning('暂无可用设备，请先部署并启动Agent')
    }
  } catch (e: any) {
    console.error('Failed to load devices:', e)
    message.error('加载设备失败: ' + (e.message || '未知错误'))
  }
}

const loadMetrics = async () => {
  if (!selectedDevice.value) return
  
  try {
    const { data } = await api.get(`/performance/metrics/latest?device_id=${selectedDevice.value}`, {
      retry: 3,
      retryDelay: 1000
    } as any)
    
    currentMetrics.value = metricConfig.map(config => {
      const key = config.key
      let value = 0
      let peak = 0
      let avg = 0
      
      if (key === 'cpu') {
        value = data.cpu_percent || 0
        // 计算 memory_percent 如果为 null
        if (data.memory_used_mb && data.memory_available_mb) {
          const total = data.memory_used_mb + data.memory_available_mb
          value = data.cpu_percent || 0
          peak = data.cpu_percent || 0
          avg = data.cpu_percent || 0
        }
      } else if (key === 'gpu') {
        value = data.gpu_percent || 0
        peak = data.gpu_percent || 0
        avg = data.gpu_percent || 0
      } else if (key === 'memory') {
        // 如果 memory_percent 为 null，手动计算
        if (data.memory_percent) {
          value = data.memory_percent
          peak = data.memory_percent
          avg = data.memory_percent
        } else if (data.memory_used_mb && data.memory_available_mb) {
          const total = data.memory_used_mb + data.memory_available_mb
          value = total > 0 ? (data.memory_used_mb / total * 100) : 0
          peak = value
          avg = value
        }
      } else if (key === 'disk') {
        value = ((data.disk_read_mbps || 0) + (data.disk_write_mbps || 0)) / 2
        peak = value
        avg = value
      }
      
      return {
        ...config,
        value: config.key === 'disk' ? value.toFixed(1) : value.toFixed(1),
        percentage: Number(Math.min(value, 100).toFixed(1)),
        peak: config.key === 'disk' ? peak.toFixed(1) : peak.toFixed(1),
        avg: config.key === 'disk' ? avg.toFixed(1) : avg.toFixed(1)
      }
    })
  } catch (e: any) {
    console.error('Failed to load metrics:', e)
    // 如果是404错误，说明没有数据，不显示错误而是显示提示
    if (e.response?.status === 404) {
      message.info('暂无性能数据，请确保Agent已启动并正在上报数据')
    } else {
      message.error('加载指标失败: ' + (e.message || ''))
    }
  }
}

const loadBenchmarks = async () => {
  if (!selectedDevice.value) return
  
  benchmarkLoading.value = true
  try {
    const { data } = await api.get(`/performance/benchmarks?device_id=${selectedDevice.value}&limit=10`)
    benchmarks.value = data.items || []
  } catch (e) {
    console.error('Failed to load benchmarks:', e)
  } finally {
    benchmarkLoading.value = false
  }
}

const loadAlerts = async () => {
  if (!selectedDevice.value) return
  
  try {
    const { data } = await api.get(`/performance/alerts?device_id=${selectedDevice.value}&is_resolved=false&limit=20`)
    alerts.value = data.items || []
  } catch (e) {
    console.error('Failed to load alerts:', e)
  }
}

const refreshCpuChart = async () => {
  if (!selectedDevice.value || !cpuChart) return
  const seconds = cpuTimeRange.value === '1m' ? 60 : cpuTimeRange.value === '5m' ? 300 : 900
  try {
    const { data } = await api.get(`/performance/metrics/realtime/${selectedDevice.value}?seconds=${seconds}`)
    if (data.metrics && data.metrics.length > 0) {
      const timestamps = data.metrics.map((m: any) => new Date(m.timestamp).toLocaleTimeString())
      const cpuData = data.metrics.map((m: any) => Number((m.cpu_percent || 0).toFixed(1)))
      cpuChart.setOption({
        xAxis: { data: timestamps },
        series: [{ data: cpuData }]
      })
    }
  } catch (e: any) {
    console.error('Failed to load CPU chart data:', e)
  }
}

const refreshGpuChart = async () => {
  if (!selectedDevice.value || !gpuChart) return
  const seconds = gpuTimeRange.value === '1m' ? 60 : gpuTimeRange.value === '5m' ? 300 : 900
  try {
    const { data } = await api.get(`/performance/metrics/realtime/${selectedDevice.value}?seconds=${seconds}`)
    if (data.metrics && data.metrics.length > 0) {
      const timestamps = data.metrics.map((m: any) => new Date(m.timestamp).toLocaleTimeString())
      
      let seriesData = []
      let yAxisFormatter = '{value}%'
      let seriesName = 'GPU'
      let maxVal = 100

      if (gpuMetricType.value === 'memory') {
        // VRAM usage in MB
        seriesData = data.metrics.map((m: any) => (m.gpu_memory_used_mb || 0))
        yAxisFormatter = '{value} MB'
        seriesName = '显存'
        // Dynamic max
        maxVal = Math.max(...seriesData) * 1.2 || 1024
        
        // Try to get total VRAM for better max
        if (currentDeviceInfo.value && currentDeviceInfo.value.gpu_vram_mb) {
            maxVal = currentDeviceInfo.value.gpu_vram_mb
        } else if (data.metrics[0].gpu_memory_total_mb) {
            maxVal = data.metrics[0].gpu_memory_total_mb
        }
      } else {
        // GPU Usage %
      seriesData = data.metrics.map((m: any) => Number((m.gpu_percent || 0).toFixed(1)))
      yAxisFormatter = '{value}%'
      seriesName = 'GPU'
      maxVal = 100
      }

      gpuVramHistory.value = data.metrics.map((m: any) => (m.gpu_memory_used_mb || 0) / 1024)
      
      const option: any = {
        xAxis: { data: timestamps },
        yAxis: { max: maxVal, axisLabel: { formatter: yAxisFormatter } },
        series: [{ 
            name: seriesName,
            data: seriesData,
            areaStyle: { color: 'rgba(139, 92, 246, 0.2)' }
        }]
      }

      // 显存模式下，不需要设置 max 为 100，如果是 usage 则需要
      if (gpuMetricType.value === 'memory') {
         delete option.yAxis.max
         option.yAxis.axisLabel.formatter = '{value} MB'
         // 但如果能拿到显存上限，最好设置一下
         if (currentDeviceInfo.value && currentDeviceInfo.value.gpu_vram_mb) {
             option.yAxis.max = currentDeviceInfo.value.gpu_vram_mb
         }
      } else {
        option.yAxis.max = 100
        option.yAxis.axisLabel.formatter = '{value}%'
      }

      gpuChart.setOption(option)
    }
  } catch (e: any) {
    console.error('Failed to load GPU chart data:', e)
  }
}

const refreshMemoryChart = async () => {
  if (!selectedDevice.value || !memoryChart) return
  const seconds = memoryTimeRange.value === '1m' ? 60 : memoryTimeRange.value === '5m' ? 300 : 900
  try {
    const { data } = await api.get(`/performance/metrics/realtime/${selectedDevice.value}?seconds=${seconds}`)
    if (data.metrics && data.metrics.length > 0) {
      const timestamps = data.metrics.map((m: any) => new Date(m.timestamp).toLocaleTimeString())
      const memoryData = data.metrics.map((m: any) => {
        if (m.memory_percent) return Number(m.memory_percent.toFixed(1))
        if (m.memory_used_mb && m.memory_available_mb) {
          const total = m.memory_used_mb + m.memory_available_mb
          return total > 0 ? Number((m.memory_used_mb / total * 100).toFixed(1)) : 0
        }
        return 0
      })
      memoryChart.setOption({
        xAxis: { data: timestamps },
        series: [{ data: memoryData }]
      })
    }
  } catch (e: any) {
    console.error('Failed to load Memory chart data:', e)
  }
}

const refreshDiskChart = async () => {
  if (!selectedDevice.value || !diskIOChart) return
  const seconds = diskTimeRange.value === '1m' ? 60 : diskTimeRange.value === '5m' ? 300 : 900
  try {
    const { data } = await api.get(`/performance/metrics/realtime/${selectedDevice.value}?seconds=${seconds}`)
    if (data.metrics && data.metrics.length > 0) {
      const timestamps = data.metrics.map((m: any) => new Date(m.timestamp).toLocaleTimeString())
      
      // 更新磁盘选项
      const allDisks = new Set<string>()
      data.metrics.forEach((m: any) => {
        if (m.disk_io_details && Array.isArray(m.disk_io_details)) {
          m.disk_io_details.forEach((d: any) => allDisks.add(d.name))
        }
      })
      if (allDisks.size > 0) {
        const options = [{ label: '所有磁盘', value: 'all' }]
        Array.from(allDisks).sort().forEach(name => {
          // 过滤掉 _Total，因为已有"所有磁盘"选项，且 _Total 在此处略显冗余
          if (name.includes('_Total')) return

          // 移除开头的数字索引 (例如 "0 C:" -> "C:")
          const label = name.replace(/^\d+\s+/, '')
          options.push({ label: label, value: name })
        })
        // 只有当当前选项不在列表中时才重置
        if (!options.find(o => o.value === selectedDisk.value)) {
           // Keep selection if valid, otherwise default to all
        }
        diskOptions.value = options
      }

      let series = []
      let yAxisFormatter: any = '{value}'

      if (diskMetricType.value === 'throughput') {
        yAxisFormatter = (value: number) => {
            if (value >= 1024) return (value / 1024).toFixed(1) + ' GB/s'
            return value.toFixed(1) + ' MB/s'
        }
        if (selectedDisk.value === 'all') {
          const diskReadData = data.metrics.map((m: any) => m.disk_read_mbps || 0)
          const diskWriteData = data.metrics.map((m: any) => m.disk_write_mbps || 0)
          series = [
            {
              name: '总读取',
              type: 'line',
              smooth: true,
              areaStyle: { color: 'rgba(245, 158, 11, 0.2)' },
              lineStyle: { color: '#f59e0b' },
              itemStyle: { color: '#f59e0b' },
              data: diskReadData
            },
            {
              name: '总写入',
              type: 'line',
              smooth: true,
              areaStyle: { color: 'rgba(239, 68, 68, 0.2)' },
              lineStyle: { color: '#ef4444' },
              itemStyle: { color: '#ef4444' },
              data: diskWriteData
            }
          ]
        } else {
          // Specific disk throughput
          const diskReadData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details)) return 0
            const detail = m.disk_io_details.find((d: any) => d.name === selectedDisk.value)
            return detail ? (detail.read_bytes_sec / 1024 / 1024).toFixed(2) : 0
          })
          const diskWriteData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details)) return 0
            const detail = m.disk_io_details.find((d: any) => d.name === selectedDisk.value)
            return detail ? (detail.write_bytes_sec / 1024 / 1024).toFixed(2) : 0
          })
          series = [
            {
              name: '读取',
              type: 'line',
              smooth: true,
              lineStyle: { color: '#f59e0b' },
              data: diskReadData
            },
            {
              name: '写入',
              type: 'line',
              smooth: true,
              lineStyle: { color: '#ef4444' },
              data: diskWriteData
            }
          ]
        }
      } else if (diskMetricType.value === 'iops') {
        yAxisFormatter = '{value}'
        // Show Queue Length
        if (selectedDisk.value === 'all') {
          // Average queue length across all disks? Or sum?
          // Let's show avg queue length sum
           const queueData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details)) return 0
            return m.disk_io_details.reduce((acc: number, d: any) => acc + (d.queue_length || 0), 0).toFixed(2)
          })
          series = [{
            name: '总队列长度',
            type: 'line',
            smooth: true,
            areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
            lineStyle: { color: '#3b82f6' },
            data: queueData
          }]
        } else {
           const queueData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details)) return 0
            const detail = m.disk_io_details.find((d: any) => d.name === selectedDisk.value)
            return detail ? (detail.queue_length || 0).toFixed(2) : 0
          })
          series = [{
            name: '队列长度',
            type: 'line',
            smooth: true,
            areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
            lineStyle: { color: '#3b82f6' },
            data: queueData
          }]
        }
      } else if (diskMetricType.value === 'latency') {
        yAxisFormatter = '{value} ms'
        if (selectedDisk.value === 'all') {
           // Avg latency
           const latencyData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details) || m.disk_io_details.length === 0) return 0
            const total = m.disk_io_details.reduce((acc: number, d: any) => acc + (d.latency_ms || 0), 0)
            return (total / m.disk_io_details.length).toFixed(2)
          })
          series = [{
            name: '平均延迟',
            type: 'line',
            smooth: true,
            areaStyle: { color: 'rgba(16, 185, 129, 0.2)' },
            lineStyle: { color: '#10b981' },
            data: latencyData
          }]
        } else {
           const latencyData = data.metrics.map((m: any) => {
            if (!m.disk_io_details || !Array.isArray(m.disk_io_details)) return 0
            const detail = m.disk_io_details.find((d: any) => d.name === selectedDisk.value)
            return detail ? (detail.latency_ms || 0).toFixed(2) : 0
          })
          series = [{
            name: '延迟',
            type: 'line',
            smooth: true,
            areaStyle: { color: 'rgba(16, 185, 129, 0.2)' },
            lineStyle: { color: '#10b981' },
            data: latencyData
          }]
        }
      }

      diskIOChart.setOption({
        xAxis: { data: timestamps },
        yAxis: { type: 'value', axisLabel: { formatter: yAxisFormatter } },
        series: series,
        legend: { show: true, top: 0, itemWidth: 8, itemHeight: 8, data: series.map(s => s.name) } // Ensure legend is shown
      }, { replaceMerge: ['series'] }) // merge: true (but here we want replace somewhat, so verify) 
    }
  } catch (e: any) {
    console.error('Failed to load Disk chart data:', e)
  }
}

const refreshCharts = async () => {
  await Promise.all([
    refreshCpuChart(),
    refreshGpuChart(),
    refreshMemoryChart(),
    refreshDiskChart()
  ])
}

const initCharts = () => {
  if (cpuChartRef.value) {
    cpuChart = echarts.init(cpuChartRef.value)
    cpuChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{
        name: 'CPU',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
        lineStyle: { color: '#3b82f6' },
        itemStyle: { color: '#3b82f6' },
        data: []
      }]
    })
  }
  
  if (gpuChartRef.value) {
    gpuChart = echarts.init(gpuChartRef.value)
    gpuChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{
        name: 'GPU',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(139, 92, 246, 0.2)' },
        lineStyle: { color: '#8b5cf6' },
        itemStyle: { color: '#8b5cf6' },
        data: []
      }]
    })
  }
  
  if (memoryChartRef.value) {
    memoryChart = echarts.init(memoryChartRef.value)
    memoryChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{
        name: '内存',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(16, 185, 129, 0.2)' },
        lineStyle: { color: '#10b981' },
        itemStyle: { color: '#10b981' },
        data: []
      }]
    })
  }
  
  if (diskIOChartRef.value) {
    diskIOChart = echarts.init(diskIOChartRef.value)
    diskIOChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 30, bottom: 20 },
      xAxis: { type: 'category', data: [] },
      yAxis: { 
        type: 'value', 
        splitNumber: 3, 
        axisLabel: { 
          formatter: (value: number) => {
            if (value >= 1024) return (value / 1024).toFixed(1) + ' GB/s'
            return value + ' MB/s'
          }
        } 
      },
      series: [
        {
          name: '读取',
          type: 'line',
          smooth: true,
          areaStyle: { color: 'rgba(245, 158, 11, 0.2)' },
          lineStyle: { color: '#f59e0b' },
          itemStyle: { color: '#f59e0b' },
          data: []
        },
        {
          name: '写入',
          type: 'line',
          smooth: true,
          areaStyle: { color: 'rgba(239, 68, 68, 0.2)' },
          lineStyle: { color: '#ef4444' },
          itemStyle: { color: '#ef4444' },
          data: []
        }
      ]
    })
  }
}

const onDeviceChange = () => {
  // Update device info when selection changes
  const device = deviceOptions.value.find(d => d.value === selectedDevice.value)
  if (device) {
    currentDeviceInfo.value = device
  }
  loadMetrics()
  loadBenchmarks()
  loadAlerts()
  refreshCharts()
  loadProcesses()
}

const refreshData = () => {
  loadMetrics()
  loadBenchmarks()
  loadAlerts()
  refreshCharts()
  loadProcesses()
  refreshWidgetData()
}

const runAIAnalysis = async () => {
  if (!selectedDevice.value) return
  
  aiLoading.value = true
  try {
    const { data } = await api.post(`/ai/analyze/metrics?device_id=${selectedDevice.value}&seconds=300`)
    aiAnalysis.value = data
  } catch (e) {
    console.error('Failed to run AI analysis:', e)
  } finally {
    aiLoading.value = false
  }
}

const startBenchmark = async () => {
  if (!selectedDevice.value || !benchmarkForm.software_code || !benchmarkForm.benchmark_type) return
  
  startingBenchmark.value = true
  try {
    await api.post('/performance/benchmarks/start', {
      device_id: selectedDevice.value,
      software_code: benchmarkForm.software_code,
      benchmark_type: benchmarkForm.benchmark_type,
      test_scene: benchmarkForm.test_scene,
      pre_flight_check: benchmarkForm.pre_flight_check,
      resource_limit_cpu: benchmarkForm.resource_limit_cpu,
      resource_limit_mem: benchmarkForm.resource_limit_mem
    })
    showBenchmarkModal.value = false
    loadBenchmarks()
  } catch (e) {
    console.error('Failed to start benchmark:', e)
  } finally {
    startingBenchmark.value = false
  }
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

let refreshInterval: number | null = null

onMounted(async () => {
  await loadDevices()
  initCharts()
  if (selectedDevice.value) {
    await onDeviceChange()
    refreshInterval = window.setInterval(refreshData, 10000)
  }
  loadSavedWidgets()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (cpuChart) cpuChart.dispose()
  if (gpuChart) gpuChart.dispose()
  if (memoryChart) memoryChart.dispose()
  if (diskIOChart) diskIOChart.dispose()
})
</script>

<style scoped>
.performance-page {
  padding: 20px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.device-info-section {
  margin-bottom: 24px;
}

/* Fix text visibility on white background */
.header-right :deep(.n-base-selection-label),
.header-right :deep(.n-base-selection-placeholder),
.header-right :deep(.n-base-selection-input) {
  color: #333 !important; 
  --n-text-color: #333 !important;
  --n-placeholder-color: #999 !important;
}

.header-right :deep(.n-base-selection) {
  --n-border: 1px solid #e2e8f0 !important;
  background-color: #fff !important;
}

/* Fix button text visibility */
.header-right :deep(.n-button:not(.n-button--primary)) {
  color: #333 !important;
  --n-text-color: #333 !important;
  background-color: #f1f5f9 !important;
}

/* Fix modal and form text visibility */
:deep(.n-modal), :deep(.n-card), :deep(.n-form-item-label) {
  color: #333 !important;
  --n-text-color: #333 !important;
}

.metrics-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-title {
  font-size: 14px;
  color: #64748b;
}

.metric-value {
  margin-bottom: 12px;
}

.metric-value .value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.metric-value .unit {
  font-size: 14px;
  color: #64748b;
  margin-left: 4px;
}

.metric-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.process-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.widget-board {
  margin-bottom: 24px;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.widget-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.widget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.widget-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.widget-card h4 {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 12px 0;
}

/* Table border styling */
:deep(.n-data-table) {
  --n-border: 1px solid #e2e8f0 !important;
}

:deep(.n-data-table-th) {
  border-bottom: 1px solid #e2e8f0 !important;
  background-color: #f8fafc !important;
  padding: 12px !important;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid #e2e8f0 !important;
  padding: 12px !important;
}

:deep(.n-data-table-tr:hover) {
  background-color: #f8fafc !important;
}

/* Benchmarks card table */
.benchmarks-card :deep(.n-data-table) {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.bottom-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.benchmarks-card,
.analysis-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.analysis-content {
  min-height: 150px;
}

.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendations {
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
}

.recommendations h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #0369a1;
}

.recommendations p {
  margin: 0;
  font-size: 14px;
  color: #075985;
}

.analysis-empty {
  padding: 40px 0;
}

.alerts-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}

.alert-item.warning {
  background: #fffbeb;
  border-left-color: #f59e0b;
}

.alert-item.info {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.alert-icon {
  color: #ef4444;
}

.alert-item.warning .alert-icon {
  color: #f59e0b;
}

.alert-item.info .alert-icon {
  color: #3b82f6;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.alert-message {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.alert-time {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
}
</style>
