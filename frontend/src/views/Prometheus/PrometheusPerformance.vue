<template>
  <div class="prometheus-performance">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">性能监控 (Prometheus)</h1>
        <span class="page-subtitle">基于 Prometheus 的实时硬件性能监控</span>
      </div>
      <div class="header-right">
        <n-select
          v-model:value="selectedInstance"
          :options="instanceOptions"
          placeholder="选择设备"
          style="width: 200px"
          @update:value="onInstanceChange"
        />
        <n-button type="primary" @click="refreshData" :loading="loading">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </header>

    <!-- Prometheus Status -->
    <nAlert v-if="!prometheusAvailable" type="warning" title="Prometheus 不可用" style="margin-bottom: 16px;">
      请确保 Prometheus 服务正在运行，并且已配置 windows_exporter。
      <template #action>
        <n-button size="small" @click="checkPrometheusStatus">重试</n-button>
      </template>
    </nAlert>

    <!-- Quick Stats Cards -->
    <section class="quick-stats" v-if="prometheusAvailable">
      <n-grid :cols="4" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-card class="stat-card" size="small">
            <div class="stat-label">CPU 使用率</div>
            <div class="stat-value" :class="getMetricClass(currentMetrics.cpu)">
              {{ currentMetrics.cpu !== null ? currentMetrics.cpu.toFixed(1) : 'N/A' }}%
            </div>
            <n-progress
              type="line"
              :percentage="currentMetrics.cpu || 0"
              :color="getMetricColor(currentMetrics.cpu)"
              :height="8"
            />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card" size="small">
            <div class="stat-label">内存使用率</div>
            <div class="stat-value" :class="getMetricClass(currentMetrics.memory)">
              {{ currentMetrics.memory !== null ? currentMetrics.memory.toFixed(1) : 'N/A' }}%
            </div>
            <n-progress
              type="line"
              :percentage="currentMetrics.memory || 0"
              :color="getMetricColor(currentMetrics.memory)"
              :height="8"
            />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card" size="small">
            <div class="stat-label">GPU 使用率</div>
            <div class="stat-value" :class="getMetricClass(currentMetrics.gpu)">
              {{ currentMetrics.gpu !== null ? currentMetrics.gpu.toFixed(1) : 'N/A' }}%
            </div>
            <n-progress
              v-if="currentMetrics.gpu !== null"
              type="line"
              :percentage="currentMetrics.gpu"
              :color="getMetricColor(currentMetrics.gpu)"
              :height="8"
            />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card" size="small">
            <div class="stat-label">GPU 温度</div>
            <div class="stat-value" :class="getTempClass(currentMetrics.gpuTemp)">
              {{ currentMetrics.gpuTemp !== null ? currentMetrics.gpuTemp.toFixed(0) : 'N/A' }}°C
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </section>

    <!-- Time Range Selector -->
    <section class="time-range-section" v-if="prometheusAvailable">
      <n-radio-group v-model:value="timeRange" size="small" @update:value="refreshData">
        <n-radio-button value="5">5 分钟</n-radio-button>
        <n-radio-button value="15">15 分钟</n-radio-button>
        <n-radio-button value="30">30 分钟</n-radio-button>
        <n-radio-button value="60">1 小时</n-radio-button>
      </n-radio-group>
    </section>

    <!-- Charts Row -->
    <section class="charts-section" v-if="prometheusAvailable">
      <div class="chart-card">
        <div class="chart-header">
          <h3>CPU 使用率趋势</h3>
        </div>
        <div ref="cpuChartRef" style="height: 250px;"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>内存使用率趋势</h3>
        </div>
        <div ref="memoryChartRef" style="height: 250px;"></div>
      </div>
    </section>

    <!-- GPU Charts -->
    <section class="charts-section" v-if="prometheusAvailable && currentMetrics.gpu !== null">
      <div class="chart-card">
        <div class="chart-header">
          <h3>GPU 使用率趋势</h3>
        </div>
        <div ref="gpuChartRef" style="height: 250px;"></div>
      </div>
      <div class="chart-card" v-if="currentMetrics.gpuTemp !== null">
        <div class="chart-header">
          <h3>GPU 温度趋势</h3>
        </div>
        <div ref="gpuTempChartRef" style="height: 250px;"></div>
      </div>
    </section>

    <!-- Grafana Embed Section -->
    <section class="grafana-section" v-if="prometheusAvailable && grafanaUrl">
      <h2>Grafana 监控面板</h2>
      <GrafanaPanel
        :dashboard-uid="grafanaDashboardUid"
        :device-id="selectedInstance || undefined"
        :width="'100%'"
        :height="500"
        time-from="now-1h"
        time-to="now"
      />
    </section>

    <!-- Instance List -->
    <section class="instances-section" v-if="prometheusAvailable">
      <h2>监控实例</h2>
      <n-table :bordered="false" :single-line="false">
        <thead>
          <tr>
            <th>实例</th>
            <th>CPU</th>
            <th>内存</th>
            <th>GPU</th>
            <th>GPU 温度</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inst in instances" :key="inst.name">
            <td>{{ inst.name }}</td>
            <td>
              <n-tag v-if="inst.cpu !== null" :type="getMetricTagType(inst.cpu)">
                {{ inst.cpu.toFixed(1) }}%
              </n-tag>
              <span v-else>N/A</span>
            </td>
            <td>
              <n-tag v-if="inst.memory !== null" :type="getMetricTagType(inst.memory)">
                {{ inst.memory.toFixed(1) }}%
              </n-tag>
              <span v-else>N/A</span>
            </td>
            <td>
              <n-tag v-if="inst.gpu !== null" :type="getMetricTagType(inst.gpu)">
                {{ inst.gpu.toFixed(1) }}%
              </n-tag>
              <span v-else>N/A</span>
            </td>
            <td>
              <span v-if="inst.gpuTemp !== null" :class="getTempClass(inst.gpuTemp)">
                {{ inst.gpuTemp.toFixed(0) }}°C
              </span>
              <span v-else>N/A</span>
            </td>
            <td>
              <n-button text type="primary" @click="selectInstance(inst.name)">
                查看
              </n-button>
            </td>
          </tr>
        </tbody>
      </n-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { NButton, NIcon, NSelect, NGrid, NGi, NCard, NProgress, NAlert, NRadioGroup, NRadioButton, NTable, NTag } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import * as echarts from 'echarts'
import { usePrometheus } from '@/composables/usePrometheus'
import GrafanaPanel from '@/components/GrafanaPanel.vue'
import api from '@/api'

// Environment
const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000'
const grafanaDashboardUid = 'windows-exporter'

// State
const selectedInstance = ref<string | null>(null)
const instanceOptions = ref<{ label: string; value: string }[]>([])
const timeRange = ref('60')
const prometheusAvailable = ref(true)
const loading = ref(false)

const currentMetrics = reactive({
  cpu: null as number | null,
  memory: null as number | null,
  gpu: null as number | null,
  gpuTemp: null as number | null,
  cpuTemp: null as number | null
})

interface InstanceInfo {
  name: string
  cpu: number | null
  memory: number | null
  gpu: number | null
  gpuTemp: number | null
}

const instances = ref<InstanceInfo[]>([])

// Charts refs
const cpuChartRef = ref<HTMLElement | null>(null)
const memoryChartRef = ref<HTMLElement | null>(null)
const gpuChartRef = ref<HTMLElement | null>(null)
const gpuTempChartRef = ref<HTMLElement | null>(null)

let cpuChart: echarts.ECharts | null = null
let memoryChart: echarts.ECharts | null = null
let gpuChart: echarts.ECharts | null = null
let gpuTempChart: echarts.ECharts | null = null

// Prometheus hook
const { getCpuPercent, getMemoryPercent, getGpuMetrics, getLatestMetrics, checkStatus } = usePrometheus()

// Methods
const getMetricClass = (value: number | null): string => {
  if (value === null) return ''
  if (value >= 90) return 'metric-critical'
  if (value >= 70) return 'metric-warning'
  return 'metric-normal'
}

const getMetricColor = (value: number | null): string => {
  if (value === null) return '#999'
  if (value >= 90) return '#f03838'
  if (value >= 70) return '#f0a038'
  return '#38f038'
}

const getMetricTagType = (value: number | null): 'success' | 'warning' | 'error' => {
  if (value === null) return 'success'
  if (value >= 90) return 'error'
  if (value >= 70) return 'warning'
  return 'success'
}

const getTempClass = (value: number | null): string => {
  if (value === null) return ''
  if (value >= 85) return 'temp-critical'
  if (value >= 75) return 'temp-warning'
  return 'temp-normal'
}

const checkPrometheusStatus = async () => {
  prometheusAvailable.value = await checkStatus()
}

const loadDevices = async () => {
  try {
    const { data } = await api.get('/devices', { params: { limit: 100 } })
    if (data.items) {
      instanceOptions.value = data.items.map((d: any) => ({
        label: d.device_name || d.hostname || d.id,
        value: d.hostname || d.ip_address || d.id
      }))
      
      if (instanceOptions.value.length > 0 && !selectedInstance.value) {
        selectedInstance.value = instanceOptions.value[0].value
      }
    }
  } catch (e) {
    console.error('Failed to load devices:', e)
  }
}

const loadAllInstancesMetrics = async () => {
  if (instanceOptions.value.length === 0) return
  
  const metricsPromises = instanceOptions.value.map(async (inst) => {
    try {
      const metrics = await getLatestMetrics(inst.value)
      return {
        name: inst.label,
        cpu: metrics.cpu,
        memory: metrics.memory,
        gpu: metrics.gpu,
        gpuTemp: metrics.gpuTemp
      }
    } catch {
      return {
        name: inst.label,
        cpu: null,
        memory: null,
        gpu: null,
        gpuTemp: null
      }
    }
  })
  
  instances.value = await Promise.all(metricsPromises)
}

const refreshData = async () => {
  if (!selectedInstance.value) return
  
  loading.value = true
  try {
    const minutes = parseInt(timeRange.value)
    
    // Get current values
    const metrics = await getLatestMetrics(selectedInstance.value)
    currentMetrics.cpu = metrics.cpu
    currentMetrics.memory = metrics.memory
    currentMetrics.gpu = metrics.gpu
    currentMetrics.gpuTemp = metrics.gpuTemp
    currentMetrics.cpuTemp = metrics.cpuTemp
    
    // Get historical data
    const [cpuData, memoryData, gpuData] = await Promise.all([
      getCpuPercent(selectedInstance.value, minutes),
      getMemoryPercent(selectedInstance.value, minutes),
      getGpuMetrics(selectedInstance.value, minutes)
    ])
    
    // Update charts
    updateCpuChart(cpuData)
    updateMemoryChart(memoryData)
    updateGpuChart(gpuData.utilization)
    
    if (gpuData.temperature.length > 0) {
      updateGpuTempChart(gpuData.temperature)
    }
    
    // Refresh instance list
    await loadAllInstancesMetrics()
  } catch (e) {
    console.error('Failed to refresh data:', e)
  } finally {
    loading.value = false
  }
}

const updateCpuChart = (data: any[]) => {
  if (!cpuChartRef.value) return
  
  if (!cpuChart) {
    cpuChart = echarts.init(cpuChartRef.value)
  }
  
  const seriesData = data.flatMap(item => 
    item.points.map(p => [p.timestamp, p.value])
  )
  
  cpuChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'time' },
    yAxis: { type: 'value', max: 100, name: '%' },
    series: [{
      name: 'CPU',
      type: 'line',
      data: seriesData,
      smooth: true,
      lineStyle: { color: '#18A058' },
      areaStyle: { color: 'rgba(24, 160, 88, 0.2)' }
    }]
  })
}

const updateMemoryChart = (data: any[]) => {
  if (!memoryChartRef.value) return
  
  if (!memoryChart) {
    memoryChart = echarts.init(memoryChartRef.value)
  }
  
  const seriesData = data.flatMap(item => 
    item.points.map(p => [p.timestamp, p.value])
  )
  
  memoryChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'time' },
    yAxis: { type: 'value', max: 100, name: '%' },
    series: [{
      name: 'Memory',
      type: 'line',
      data: seriesData,
      smooth: true,
      lineStyle: { color: '#2080F0' },
      areaStyle: { color: 'rgba(32, 128, 240, 0.2)' }
    }]
  })
}

const updateGpuChart = (data: any[]) => {
  if (!gpuChartRef.value) return
  
  if (!gpuChart) {
    gpuChart = echarts.init(gpuChartRef.value)
  }
  
  const seriesData = data.flatMap(item => 
    item.points.map(p => [p.timestamp, p.value])
  )
  
  gpuChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'time' },
    yAxis: { type: 'value', max: 100, name: '%' },
    series: [{
      name: 'GPU',
      type: 'line',
      data: seriesData,
      smooth: true,
      lineStyle: { color: '#F0A238' },
      areaStyle: { color: 'rgba(240, 162, 56, 0.2)' }
    }]
  })
}

const updateGpuTempChart = (data: any[]) => {
  if (!gpuTempChartRef.value) return
  
  if (!gpuTempChart) {
    gpuTempChart = echarts.init(gpuTempChartRef.value)
  }
  
  const seriesData = data.flatMap(item => 
    item.points.map(p => [p.timestamp, p.value])
  )
  
  gpuTempChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'time' },
    yAxis: { type: 'value', name: '°C' },
    series: [{
      name: 'GPU Temp',
      type: 'line',
      data: seriesData,
      smooth: true,
      lineStyle: { color: '#F03838' },
      areaStyle: { color: 'rgba(240, 56, 56, 0.2)' }
    }]
  })
}

const onInstanceChange = () => {
  refreshData()
}

const selectInstance = (name: string) => {
  const inst = instanceOptions.value.find(i => i.label === name)
  if (inst) {
    selectedInstance.value = inst.value
  }
}

// Lifecycle
onMounted(async () => {
  await checkPrometheusStatus()
  await loadDevices()
  if (prometheusAvailable.value) {
    await refreshData()
  }
  
  // Handle resize
  window.addEventListener('resize', () => {
    cpuChart?.resize()
    memoryChart?.resize()
    gpuChart?.resize()
    gpuTempChart?.resize()
  })
})
</script>

<style scoped>
.prometheus-performance {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-color-3);
  margin-top: 4px;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.quick-stats {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: var(--text-color-3);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 8px;
}

.metric-normal {
  color: #18A058;
}

.metric-warning {
  color: #F0A238;
}

.metric-critical {
  color: #F03838;
}

.temp-normal {
  color: #18A058;
}

.temp-warning {
  color: #F0A238;
}

.temp-critical {
  color: #F03838;
}

.time-range-section {
  margin-bottom: 24px;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.grafana-section {
  margin-bottom: 24px;
}

.grafana-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.instances-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}
</style>
