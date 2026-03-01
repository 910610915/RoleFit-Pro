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
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </header>

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
          <n-radio-group v-model:value="timeRange" size="small" @update:value="refreshCharts">
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
        </div>
        <div ref="gpuChartRef" style="height: 250px;"></div>
      </div>
    </section>

    <!-- Bottom Row -->
    <section class="bottom-section">
      <!-- Benchmarks -->
      <div class="benchmarks-card">
        <div class="card-header">
          <h3>基准测试结果</h3>
          <n-button size="small" @click="showBenchmarkModal = true">
            <template #icon><n-icon><Add /></n-icon></template>
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
              <n-empty description="点击一键分析获取AI分析结果">
                <template #extra>
                  <n-button type="primary" @click="runAIAnalysis">开始分析</n-button>
                </template>
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
      </n-form>
      <template #footer>
        <n-button @click="showBenchmarkModal = false">取消</n-button>
        <n-button type="primary" @click="startBenchmark" :loading="startingBenchmark">开始测试</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, h } from 'vue'
import { 
  NButton, NSelect, NIcon, NProgress, NRadioGroup, NRadioButton,
  NDataTable, NAlert, NSpin, NEmpty, NModal, NForm, NFormItem,
  NInput, NBadge
} from 'naive-ui'
import * as echarts from 'echarts'
import { 
  HardwareChip, Desktop, Speedometer, Server, 
  Refresh, Add, Bulb, Warning as WarningIcon, AlertCircle as AlertIcon
} from '@vicons/ionicons5'

// Map icons to metric keys
const iconMap: Record<string, any> = {
  cpu: HardwareChip,
  gpu: Desktop,
  memory: Speedometer,
  disk: Server
}

// State
const selectedDevice = ref<string | null>(null)
const deviceOptions = ref<{label: string, value: string}[]>([])
const currentMetrics = ref<any[]>([])
const timeRange = ref('5m')
const cpuChartRef = ref<HTMLElement | null>(null)
const gpuChartRef = ref<HTMLElement | null>(null)
let cpuChart: echarts.ECharts | null = null
let gpuChart: echarts.ECharts | null = null

const benchmarks = ref<any[]>([])
const benchmarkLoading = ref(false)
const showBenchmarkModal = ref(false)
const startingBenchmark = ref(false)
const benchmarkForm = reactive({
  software_code: null,
  benchmark_type: null,
  test_scene: ''
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
    const res = await fetch('/api/devices')
    const data = await res.json()
    if (data.items) {
      deviceOptions.value = data.items.map((d: any) => ({
        label: d.device_name,
        value: d.id
      }))
      if (deviceOptions.value.length > 0 && !selectedDevice.value) {
        selectedDevice.value = deviceOptions.value[0].value
      }
    }
  } catch (e) {
    console.error('Failed to load devices:', e)
  }
}

const loadMetrics = async () => {
  if (!selectedDevice.value) return
  
  try {
    const res = await fetch(`/api/performance/metrics/latest?device_id=${selectedDevice.value}`)
    const data = await res.json()
    
    currentMetrics.value = metricConfig.map(config => {
      const key = config.key
      let value = 0
      let peak = 0
      let avg = 0
      
      if (key === 'cpu') {
        value = data.cpu_percent || 0
        peak = data.cpu_percent || 0
        avg = data.cpu_percent || 0
      } else if (key === 'gpu') {
        value = data.gpu_percent || 0
        peak = data.gpu_percent || 0
        avg = data.gpu_percent || 0
      } else if (key === 'memory') {
        value = data.memory_percent || 0
        peak = data.memory_percent || 0
        avg = data.memory_percent || 0
      } else if (key === 'disk') {
        value = ((data.disk_read_mbps || 0) + (data.disk_write_mbps || 0)) / 2
        peak = value
        avg = value
      }
      
      return {
        ...config,
        value: config.key === 'disk' ? value.toFixed(1) : value.toFixed(1),
        percentage: Math.min(value, 100),
        peak: config.key === 'disk' ? peak.toFixed(1) : peak.toFixed(1),
        avg: config.key === 'disk' ? avg.toFixed(1) : avg.toFixed(1)
      }
    })
  } catch (e) {
    console.error('Failed to load metrics:', e)
  }
}

const loadBenchmarks = async () => {
  if (!selectedDevice.value) return
  
  benchmarkLoading.value = true
  try {
    const res = await fetch(`/api/performance/benchmarks?device_id=${selectedDevice.value}&limit=10`)
    const data = await res.json()
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
    const res = await fetch(`/api/performance/alerts?device_id=${selectedDevice.value}&is_resolved=false&limit=20`)
    const data = await res.json()
    alerts.value = data.items || []
  } catch (e) {
    console.error('Failed to load alerts:', e)
  }
}

const refreshCharts = async () => {
  if (!selectedDevice.value || !cpuChart || !gpuChart) return
  
  const seconds = timeRange.value === '1m' ? 60 : timeRange.value === '5m' ? 300 : 900
  
  try {
    const res = await fetch(`/api/performance/metrics/realtime/${selectedDevice.value}?seconds=${seconds}`)
    const data = await res.json()
    
    if (data.metrics && data.metrics.length > 0) {
      const timestamps = data.metrics.map((m: any) => new Date(m.timestamp).toLocaleTimeString())
      const cpuData = data.metrics.map((m: any) => m.cpu_percent || 0)
      const gpuData = data.metrics.map((m: any) => m.gpu_percent || 0)
      
      cpuChart.setOption({
        xAxis: { data: timestamps },
        series: [{ data: cpuData }]
      })
      
      gpuChart.setOption({
        xAxis: { data: timestamps },
        series: [{ data: gpuData }]
      })
    }
  } catch (e) {
    console.error('Failed to load chart data:', e)
  }
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
}

const onDeviceChange = () => {
  loadMetrics()
  loadBenchmarks()
  loadAlerts()
  refreshCharts()
}

const refreshData = () => {
  loadMetrics()
  loadBenchmarks()
  loadAlerts()
  refreshCharts()
}

const runAIAnalysis = async () => {
  if (!selectedDevice.value) return
  
  aiLoading.value = true
  try {
    const res = await fetch(`/api/ai/analyze/metrics?device_id=${selectedDevice.value}&seconds=300`, {
      method: 'POST'
    })
    const data = await res.json()
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
    await fetch('/api/performance/benchmarks/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: selectedDevice.value,
        software_code: benchmarkForm.software_code,
        benchmark_type: benchmarkForm.benchmark_type,
        test_scene: benchmarkForm.test_scene
      })
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
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (cpuChart) cpuChart.dispose()
  if (gpuChart) gpuChart.dispose()
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

.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
