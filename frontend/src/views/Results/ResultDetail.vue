<template>
  <div class="result-detail">
    <n-button @click="router.back()" class="back-btn">
      <template #icon><n-icon><arrow-back /></n-icon></template>
      返回
    </n-button>
    <n-space class="action-buttons">
      <n-button type="primary" @click="handleExport">
        <template #icon><n-icon><download /></n-icon></template>
        导出报告
      </n-button>
    </n-space>
    
    <n-spin :show="loading">
      <!-- 基本信息 -->
      <n-grid :cols="2" :x-gap="20" :y-gap="20" class="mb-5">
        <n-gi>
          <n-card title="测试概览">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="状态">
                <n-tag :type="result.test_status === 'passed' ? 'success' : result.test_status === 'failed' ? 'error' : result.test_status === 'warning' ? 'warning' : 'default'">
                  {{ result.test_status === 'passed' ? '通过' : result.test_status === 'failed' ? '失败' : result.test_status === 'warning' ? '警告' : result.test_status }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="测试类型">{{ result.test_type }}</n-descriptions-item>
              <n-descriptions-item label="总分">
                <span class="total-score">{{ result.overall_score?.toFixed(1) || '-' }}</span>
              </n-descriptions-item>
              <n-descriptions-item label="标准达标">
                <n-tag v-if="result.is_standard_met" type="success">通过</n-tag>
                <n-tag v-else type="error">未通过</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="测试时长">{{ result.duration_seconds }}秒</n-descriptions-item>
              <n-descriptions-item label="开始时间">{{ new Date(result.start_time).toLocaleString() }}</n-descriptions-item>
              <n-descriptions-item label="结束时间">{{ new Date(result.end_time).toLocaleString() }}</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
        
        <n-gi>
          <n-card title="各组件分数">
            <n-grid :cols="2" :x-gap="15" :y-gap="15">
              <n-gi v-for="score in componentScores" :key="score.key">
                <div class="score-card" :class="score.class">
                  <div class="score-value">{{ score.value }}</div>
                  <div class="score-label">{{ score.label }}</div>
                  <n-progress 
                    v-if="score.value" 
                    type="line" 
                    :percentage="Math.min(Number(score.value), 100)" 
                    :color="score.color"
                    :height="6"
                  />
                </div>
              </n-gi>
            </n-grid>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 性能趋势图表区域 -->
      <n-card title="性能监控趋势" class="mb-5">
        <n-tabs type="line" animated>
          <!-- CPU 监控 -->
          <n-tab-pane name="cpu" tab="CPU 监控">
            <n-grid :cols="3" :x-gap="15" :y-gap="15">
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">CPU 占用率</div>
                  <div ref="cpuUsageChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">CPU 温度（模拟）</div>
                  <div ref="cpuTempChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">CPU 功耗（模拟）</div>
                  <div ref="cpuPowerChart" class="chart-container"></div>
                </div>
              </n-gi>
            </n-grid>
          </n-tab-pane>
          
          <!-- GPU 监控 -->
          <n-tab-pane name="gpu" tab="GPU 监控">
            <n-grid :cols="3" :x-gap="15" :y-gap="15">
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">GPU 占用率</div>
                  <div ref="gpuUsageChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">GPU 温度（模拟）</div>
                  <div ref="gpuTempChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">GPU 显存使用</div>
                  <div ref="gpuMemoryChart" class="chart-container"></div>
                </div>
              </n-gi>
            </n-grid>
          </n-tab-pane>
          
          <!-- 内存监控 -->
          <n-tab-pane name="memory" tab="内存监控">
            <n-grid :cols="2" :x-gap="15" :y-gap="15">
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">内存使用率</div>
                  <div ref="memoryChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">内存使用量 (MB)</div>
                  <div ref="memoryMBChart" class="chart-container"></div>
                </div>
              </n-gi>
            </n-grid>
          </n-tab-pane>
          
          <!-- 磁盘监控 -->
          <n-tab-pane name="disk" tab="磁盘监控">
            <n-grid :cols="2" :x-gap="15" :y-gap="15">
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">磁盘读取速度</div>
                  <div ref="diskReadChart" class="chart-container"></div>
                </div>
              </n-gi>
              <n-gi>
                <div class="chart-card">
                  <div class="chart-title">磁盘写入速度</div>
                  <div ref="diskWriteChart" class="chart-container"></div>
                </div>
              </n-gi>
            </n-grid>
          </n-tab-pane>
          
          <!-- 综合趋势 -->
          <n-tab-pane name="overview" tab="综合趋势">
            <div class="chart-card full-width">
              <div class="chart-title">综合性能趋势</div>
              <div ref="overviewChart" class="chart-container large"></div>
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-card>

      <!-- 瓶颈和升级建议 -->
      <n-grid :cols="2" :x-gap="20" :y-gap="20">
        <n-gi v-if="result.bottleneck_type">
          <n-card title="瓶颈分析">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="瓶颈类型">
                <n-tag type="warning">
                  {{ result.bottleneck_type === 'CPU' ? '处理器' : result.bottleneck_type === 'GPU' ? '显卡' : result.bottleneck_type === 'MEMORY' ? '内存' : result.bottleneck_type === 'DISK' ? '磁盘' : result.bottleneck_type }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="瓶颈描述">
                {{ getBottleneckDesc(result.bottleneck_type) }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
        
        <n-gi v-if="result.upgrade_suggestion">
          <n-card title="升级建议">
            <n-space vertical>
              <n-li v-for="(suggestion, idx) in parseSuggestions(result.upgrade_suggestion)" :key="idx">
                <n-icon color="#18a058"><checkmark-circle /></n-icon>
                {{ suggestion }}
              </n-li>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NCard, NGrid, NGi, NDescriptions, NDescriptionsItem, NTag, NIcon, NSpin, NTabs, NTabPane, NProgress, NSpace, NLi } from 'naive-ui'
import { ArrowBack, CheckmarkCircle, Download } from '@vicons/ionicons5'
import * as echarts from 'echarts'
import { resultApi, type TestResult } from '@/api/results'

const route = useRoute()
const router = useRouter()

const resultId = route.params.id as string
const loading = ref(false)

// 图表引用
const cpuUsageChart = ref<HTMLElement>()
const cpuTempChart = ref<HTMLElement>()
const cpuPowerChart = ref<HTMLElement>()
const gpuUsageChart = ref<HTMLElement>()
const gpuTempChart = ref<HTMLElement>()
const gpuMemoryChart = ref<HTMLElement>()
const memoryChart = ref<HTMLElement>()
const memoryMBChart = ref<HTMLElement>()
const diskReadChart = ref<HTMLElement>()
const diskWriteChart = ref<HTMLElement>()
const overviewChart = ref<HTMLElement>()

const result = reactive<TestResult>({
  id: '',
  device_id: '',
  start_time: '',
  end_time: '',
  duration_seconds: 0,
  created_at: ''
})

// 模拟的性能数据（实际项目中应该从API获取）
const generateMockMetrics = () => {
  const duration = result.duration_seconds || 60
  const points = Math.min(duration, 100)
  const data: any = []
  
  for (let i = 0; i < points; i++) {
    data.push({
      time: i,
      cpuPercent: 30 + Math.random() * 50 + Math.sin(i / 10) * 20,
      cpuTemp: 45 + Math.random() * 25 + Math.sin(i / 15) * 10,
      cpuPower: 15 + Math.random() * 35 + Math.sin(i / 8) * 15,
      gpuPercent: 20 + Math.random() * 60 + Math.cos(i / 12) * 25,
      gpuTemp: 35 + Math.random() * 30 + Math.cos(i / 18) * 12,
      gpuMemory: 1024 + Math.random() * 2048 + Math.sin(i / 20) * 512,
      memoryPercent: 40 + Math.random() * 30 + Math.sin(i / 25) * 10,
      memoryMB: 8192 + Math.random() * 4096,
      diskRead: 500 + Math.random() * 1500 + Math.sin(i / 5) * 300,
      diskWrite: 300 + Math.random() * 1200 + Math.cos(i / 7) * 250,
    })
  }
  return data
}

const metricsData = ref<any[]>([])

// 组件分数
const componentScores = computed(() => [
  { key: 'cpu', label: '处理器', value: result.cpu_score?.toFixed(1), color: '#2080f0', class: 'score-cpu' },
  { key: 'gpu', label: '显卡', value: result.gpu_score?.toFixed(1), color: '#f0a020', class: 'score-gpu' },
  { key: 'memory', label: '内存', value: result.memory_score?.toFixed(1), color: '#18a058', class: 'score-memory' },
  { key: 'disk', label: '磁盘', value: result.disk_score?.toFixed(1), color: '#9c27b0', class: 'score-disk' },
])

const getBottleneckDesc = (type: string) => {
  const descs: Record<string, string> = {
    'CPU': '处理器性能不足，可能是CPU主频较低或核心数较少导致处理速度受限',
    'GPU': '显卡性能不足，可能是GPU显存较小或图形处理能力有限',
    'MEMORY': '内存容量不足或频率较低，可能导致多任务处理时性能下降',
    'DISK': '磁盘性能不足，可能是机械硬盘或SSD性能较弱'
  }
  return descs[type] || '未能明确识别瓶颈'
}

const parseSuggestions = (suggestion: any) => {
  if (Array.isArray(suggestion)) return suggestion
  if (typeof suggestion === 'string') {
    try {
      return JSON.parse(suggestion)
    } catch {
      return [suggestion]
    }
  }
  return []
}

// 创建图表
const createLineChart = (container: HTMLElement, title: string, data: number[], color: string, unit: string, showArea = true) => {
  if (!container) return
  
  const chart = echarts.init(container)
  chart.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      formatter: `{b}s<br/>${title}: ${unit === '%' ? '{c}%' : '{c} ' + unit}`
    },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((_, i) => i),
      axisLabel: { fontSize: 10 },
      name: '时间(s)',
      nameLocation: 'middle',
      nameGap: 20
    },
    yAxis: {
      type: 'value',
      name: unit,
      min: 0,
      axisLabel: { fontSize: 10 }
    },
    series: [{
      data: data,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color },
      areaStyle: showArea ? { opacity: 0.3, color } : undefined
    }]
  })
}

// 创建综合趋势图
const createOverviewChart = () => {
  if (!overviewChart.value || metricsData.value.length === 0) return
  
  const chart = echarts.init(overviewChart.value)
  chart.setOption({
    title: { show: false },
    tooltip: { trigger: 'axis' },
    legend: { data: ['CPU', 'GPU', '内存', '磁盘读取', '磁盘写入'], top: 0 },
    grid: { left: 50, right: 50, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: metricsData.value.map((_, i) => i),
      name: '时间(s)',
      nameLocation: 'middle',
      nameGap: 25
    },
    yAxis: [
      {
        type: 'value',
        name: '百分比 (%)',
        min: 0,
        max: 100
      },
      {
        type: 'value',
        name: '速度 (MB/s)',
        min: 0
      }
    ],
    series: [
      {
        name: 'CPU',
        type: 'line',
        data: metricsData.value.map(d => d.cpuPercent?.toFixed(1)),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#2080f0' }
      },
      {
        name: 'GPU',
        type: 'line',
        data: metricsData.value.map(d => d.gpuPercent?.toFixed(1)),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#f0a020' }
      },
      {
        name: '内存',
        type: 'line',
        data: metricsData.value.map(d => d.memoryPercent?.toFixed(1)),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#18a058' }
      },
      {
        name: '磁盘读取',
        type: 'line',
        yAxisIndex: 1,
        data: metricsData.value.map(d => d.diskRead?.toFixed(1)),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#9c27b0' }
      },
      {
        name: '磁盘写入',
        type: 'line',
        yAxisIndex: 1,
        data: metricsData.value.map(d => d.diskWrite?.toFixed(1)),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#e91e63' }
      }
    ]
  })
}

// 初始化所有图表
const initCharts = () => {
  if (metricsData.value.length === 0) {
    metricsData.value = generateMockMetrics()
  }
  
  nextTick(() => {
    // CPU 图表
    if (cpuUsageChart.value) {
      createLineChart(cpuUsageChart.value, 'CPU占用', 
        metricsData.value.map(d => d.cpuPercent), '#2080f0', '%')
    }
    if (cpuTempChart.value) {
      createLineChart(cpuTempChart.value, 'CPU温度', 
        metricsData.value.map(d => d.cpuTemp), '#ff5722', '°C')
    }
    if (cpuPowerChart.value) {
      createLineChart(cpuPowerChart.value, 'CPU功耗', 
        metricsData.value.map(d => d.cpuPower), '#795548', 'W')
    }
    
    // GPU 图表
    if (gpuUsageChart.value) {
      createLineChart(gpuUsageChart.value, 'GPU占用', 
        metricsData.value.map(d => d.gpuPercent), '#f0a020', '%')
    }
    if (gpuTempChart.value) {
      createLineChart(gpuTempChart.value, 'GPU温度', 
        metricsData.value.map(d => d.gpuTemp), '#e91e63', '°C')
    }
    if (gpuMemoryChart.value) {
      createLineChart(gpuMemoryChart.value, 'GPU显存', 
        metricsData.value.map(d => d.gpuMemory / 1024), '#9c27b0', 'GB')
    }
    
    // 内存图表
    if (memoryChart.value) {
      createLineChart(memoryChart.value, '内存占用', 
        metricsData.value.map(d => d.memoryPercent), '#18a058', '%')
    }
    if (memoryMBChart.value) {
      createLineChart(memoryMBChart.value, '内存使用', 
        metricsData.value.map(d => d.memoryMB), '#00bcd4', 'MB')
    }
    
    // 磁盘图表
    if (diskReadChart.value) {
      createLineChart(diskReadChart.value, '读取速度', 
        metricsData.value.map(d => d.diskRead), '#9c27b0', 'MB/s')
    }
    if (diskWriteChart.value) {
      createLineChart(diskWriteChart.value, '写入速度', 
        metricsData.value.map(d => d.diskWrite), '#e91e63', 'MB/s')
    }
    
    // 综合趋势图
    createOverviewChart()
  })
}

const loadResult = async () => {
  loading.value = true
  try {
    const res = await resultApi.get(resultId)
    Object.assign(result, res.data)
    
    // 尝试获取真实指标数据
    try {
      const metricsRes = await resultApi.getMetrics(resultId)
      if (metricsRes.data && metricsRes.data.length > 0) {
        metricsData.value = metricsRes.data
      }
    } catch (e) {
      console.log('使用模拟数据')
    }
    
    initCharts()
  } catch (error) {
    console.error('Failed to load result:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadResult()
})

// 导出报告
const handleExport = () => {
  const reportContent = `
========================================
硬件性能基准测试报告
========================================

测试概览
--------
状态: ${result.test_status}
测试类型: ${result.test_type}
总分: ${result.overall_score?.toFixed(1) || '-'}
标准达标: ${result.is_standard_met ? '通过' : '未通过'}
测试时长: ${result.duration_seconds}秒
开始时间: ${new Date(result.start_time).toLocaleString()}
结束时间: ${new Date(result.end_time).toLocaleString()}

组件分数
--------
处理器: ${result.cpu_score?.toFixed(1) || '-'}
显卡: ${result.gpu_score?.toFixed(1) || '-'}
内存: ${result.memory_score?.toFixed(1) || '-'}
磁盘: ${result.disk_score?.toFixed(1) || '-'}

${result.bottleneck_type ? `瓶颈分析
--------
类型: ${result.bottleneck_type}
描述: ${getBottleneckDesc(result.bottleneck_type)}` : ''}

${result.upgrade_suggestion ? `升级建议
--------
${parseSuggestions(result.upgrade_suggestion).map((s: string) => '- ' + s).join('\n')}` : ''}

========================================
生成时间: ${new Date().toLocaleString()}
========================================
  `
  
  const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `性能测试报告_${result.id.slice(0,8)}_${new Date().toISOString().slice(0,10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.result-detail {
  padding: 20px;
}

.back-btn {
  margin-bottom: 20px;
}

.action-buttons {
  margin-left: 10px;
  margin-bottom: 20px;
}

.mb-5 {
  margin-bottom: 20px;
}

.total-score {
  font-size: 24px;
  font-weight: bold;
  color: #2080f0;
}

.score-card {
  text-align: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.score-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.score-cpu { border-left: 4px solid #2080f0; }
.score-gpu { border-left: 4px solid #f0a020; }
.score-memory { border-left: 4px solid #18a058; }
.score-disk { border-left: 4px solid #9c27b0; }

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.score-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.chart-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 15px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  text-align: center;
}

.chart-container {
  height: 180px;
  width: 100%;
}

.chart-container.large {
  height: 300px;
}

.full-width {
  width: 100%;
}
</style>
