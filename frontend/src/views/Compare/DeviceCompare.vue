<template>
  <div class="device-compare">
    <n-h1>设备性能对比</n-h1>
    
    <!-- 设备选择 -->
    <n-card title="选择对比设备" class="mb-5">
      <n-space vertical>
        <n-select
          v-model:value="selectedDevices"
          multiple
          filterable
          placeholder="选择要对比的设备（最多5台）"
          :options="deviceOptions"
          :max-tag-count="5"
        />
        <n-button type="primary" @click="loadComparison" :loading="loading" :disabled="selectedDevices.length < 2">
          <template #icon><n-icon><bar-chart /></n-icon></template>
          开始对比
        </n-button>
      </n-space>
    </n-card>

    <!-- 对比结果 -->
    <div v-if="comparisonData.length > 0">
      <!-- 总分对比 -->
      <n-card title="综合分数对比" class="mb-5">
        <n-grid :cols="comparisonData.length" :x-gap="20" :y-gap="20">
          <n-gi v-for="device in comparisonData" :key="device.device_id">
            <div class="device-score-card">
              <div class="device-name">{{ device.device_name }}</div>
              <div class="total-score">{{ device.latest_result?.calculated_overall?.toFixed(1) || device.latest_result?.overall_score?.toFixed(1) || '-' }}</div>
              <div class="score-label">综合分数</div>
              <n-progress 
                v-if="device.latest_result?.calculated_overall || device.latest_result?.overall_score"
                type="circle"
                :percentage="Math.min(device.latest_result?.calculated_overall || device.latest_result?.overall_score, 100)"
                :color="getScoreColor(device.latest_result?.calculated_overall || device.latest_result?.overall_score)"
              />
            </div>
          </n-gi>
        </n-grid>
      </n-card>

      <!-- 组件分数对比 -->
      <n-card title="组件分数对比" class="mb-5">
        <n-tabs type="line" animated @update:value="handleTabChange">
          <n-tab-pane name="bar" tab="柱状图">
            <div ref="barChart" class="chart-container"></div>
          </n-tab-pane>
          <n-tab-pane name="radar" tab="雷达图">
            <div ref="radarChart" class="chart-container"></div>
          </n-tab-pane>
        </n-tabs>
      </n-card>

      <!-- 详细数据 -->
      <n-card title="详细数据对比">
        <n-data-table
          :columns="columns"
          :data="tableData"
          :bordered="false"
        />
      </n-card>

      <!-- 硬件配置 -->
      <n-card title="硬件配置对比" class="mt-5">
        <n-grid :cols="comparisonData.length" :x-gap="20">
          <n-gi v-for="device in comparisonData" :key="device.device_id">
            <n-card size="small">
              <n-descriptions :column="1" label-placement="left" size="small">
                <n-descriptions-item label="设备名称">{{ device.device_name }}</n-descriptions-item>
                <n-descriptions-item label="CPU">{{ device.cpu_model || '-' }}</n-descriptions-item>
                <n-descriptions-item label="GPU">{{ device.gpu_model || '-' }}</n-descriptions-item>
                <n-descriptions-item label="内存">{{ device.ram_total_gb ? device.ram_total_gb + ' GB' : '-' }}</n-descriptions-item>
                <n-descriptions-item label="测试次数">{{ device.statistics?.test_count || 0 }} 次</n-descriptions-item>
                <n-descriptions-item label="平均分">{{ device.statistics?.average_score?.toFixed(1) || '-' }}</n-descriptions-item>
              </n-descriptions>
            </n-card>
          </n-gi>
        </n-grid>
      </n-card>
    </div>

    <!-- 空状态 -->
    <n-empty v-else description="请选择至少2台设备进行对比" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { NCard, NH1, NSelect, NButton, NIcon, NSpace, NTabs, NTabPane, NProgress, NDataTable, NDescriptions, NDescriptionsItem, NGrid, NGi, NEmpty } from 'naive-ui'
import { BarChart } from '@vicons/ionicons5'
import * as echarts from 'echarts'
import { deviceApi } from '@/api/devices'
import { resultApi } from '@/api/results'

// 分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 90) return '#18a058'
  if (score >= 70) return '#2080f0'
  if (score >= 50) return '#f0a020'
  return '#d03050'
}

const loading = ref(false)
const selectedDevices = ref<string[]>([])
const deviceOptions = ref<{label: string, value: string}[]>([])
const comparisonData = ref<any[]>([])

// 图表引用
const barChart = ref<HTMLElement>()
const radarChart = ref<HTMLElement>()
const activeTab = ref('bar')

// 表格列和数据
const columns = computed(() => {
  const base = [{ title: '指标', key: 'metric' }]
  const deviceCols = comparisonData.value.map(d => ({ title: d.device_name, key: d.device_id }))
  return [...base, ...deviceCols]
})

const tableData = computed(() => {
  const metrics = [
    { metric: '综合分数', key: 'overall' },
    { metric: 'CPU', key: 'cpu' },
    { metric: 'GPU', key: 'gpu' },
    { metric: '内存', key: 'memory' },
    { metric: '磁盘', key: 'disk' }
  ]
  
  return metrics.map(m => {
    const row: any = { metric: m.metric }
    comparisonData.value.forEach(d => {
      if (m.key === 'overall') {
        row[d.device_id] = d.latest_result?.calculated_overall?.toFixed(1) || d.latest_result?.overall_score?.toFixed(1) || '-'
      } else if (m.key === 'cpu') {
        row[d.device_id] = d.latest_result?.cpu_score || '-'
      } else if (m.key === 'gpu') {
        row[d.device_id] = d.latest_result?.gpu_score || '-'
      } else if (m.key === 'memory') {
        row[d.device_id] = d.latest_result?.memory_score || '-'
      } else if (m.key === 'disk') {
        row[d.device_id] = d.latest_result?.disk_score || '-'
      }
    })
    return row
  })
})

// 渲染柱状图
const renderBarChart = () => {
  if (!barChart.value || comparisonData.value.length === 0) return
  
  const chart = echarts.getInstanceByDom(barChart.value) || echarts.init(barChart.value)
  
  const categories = comparisonData.value.map(d => d.device_name)
  const cpuScores = comparisonData.value.map(d => d.latest_result?.cpu_score || 0)
  const gpuScores = comparisonData.value.map(d => d.latest_result?.gpu_score || 0)
  const memoryScores = comparisonData.value.map(d => d.latest_result?.memory_score || 0)
  const diskScores = comparisonData.value.map(d => d.latest_result?.disk_score || 0)
  
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['CPU', 'GPU', '内存', '磁盘'], top: 0 },
    grid: { left: 80, right: 80, top: 40, bottom: 40 },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: categories },
    series: [
      { 
        name: 'CPU', 
        type: 'bar', 
        data: cpuScores, 
        itemStyle: { color: '#2080f0' },
        label: { show: true, position: 'right', formatter: '{c}' }
      },
      { 
        name: 'GPU', 
        type: 'bar', 
        data: gpuScores, 
        itemStyle: { color: '#f0a020' },
        label: { show: true, position: 'right', formatter: '{c}' }
      },
      { 
        name: '内存', 
        type: 'bar', 
        data: memoryScores, 
        itemStyle: { color: '#18a058' },
        label: { show: true, position: 'right', formatter: '{c}' }
      },
      { 
        name: '磁盘', 
        type: 'bar', 
        data: diskScores, 
        itemStyle: { color: '#9c27b0' },
        label: { show: true, position: 'right', formatter: '{c}' }
      },
    ]
  })
  
  // 延迟resize确保DOM已渲染
  setTimeout(() => chart.resize(), 100)
}

// 渲染雷达图
const renderRadarChart = () => {
  if (!radarChart.value || comparisonData.value.length === 0) return
  
  const chart = echarts.getInstanceByDom(radarChart.value) || echarts.init(radarChart.value)
  
  const indicator = [
    { name: 'CPU', max: 100 },
    { name: 'GPU', max: 100 },
    { name: '内存', max: 100 },
    { name: '磁盘', max: 100 },
  ]
  
  const series = comparisonData.value.map((d, idx) => ({
    value: [
      d.latest_result?.cpu_score || 0,
      d.latest_result?.gpu_score || 0,
      d.latest_result?.memory_score || 0,
      d.latest_result?.disk_score || 0,
    ],
    name: d.device_name,
    type: 'radar',
    itemStyle: { color: ['#2080f0', '#f0a020', '#18a058', '#9c27b0', '#e91e63'][idx % 5] },
    areaStyle: { opacity: 0.1 }
  }))
  
  chart.setOption({
    tooltip: {},
    legend: { data: comparisonData.value.map(d => d.device_name), top: 0 },
    radar: { indicator, radius: '60%' },
    series: [{ type: 'radar', data: series }]
  })
  
  // 延迟resize确保DOM已渲染
  setTimeout(() => chart.resize(), 100)
}

// Tab切换时重新渲染图表
const handleTabChange = (tab: string) => {
  activeTab.value = tab
  setTimeout(() => {
    if (tab === 'bar' && barChart.value) {
      renderBarChart()
    } else if (tab === 'radar' && radarChart.value) {
      renderRadarChart()
    }
  }, 100)
}

const loadDevices = async () => {
  try {
    console.log('Loading devices...')
    const res = await deviceApi.list({ page_size: 100 })
    console.log('Devices response:', res)
    console.log('Devices data:', res?.data)
    deviceOptions.value = res.data.items.map((d: any) => ({
      label: d.device_name,
      value: d.id
    }))
    console.log('Device options:', deviceOptions.value)
  } catch (error) {
    console.error('Failed to load devices:', error)
    console.error('Error:', error.response?.data)
  }
}

const loadComparison = async () => {
  if (selectedDevices.value.length < 2) return
  
  console.log('Selected devices:', selectedDevices.value)
  console.log('Device IDs:', selectedDevices.value)
  
  loading.value = true
  try {
    console.log('Loading comparison for devices:', selectedDevices.value)
    const res = await resultApi.compareDevices(selectedDevices.value)
    console.log('API response:', res)
    console.log('Response data:', res?.data)
    
    // Handle both direct data and wrapped response
    comparisonData.value = res?.data || res
    
    console.log('Comparison data:', comparisonData.value)
    
    // 延迟渲染图表
    nextTick(() => {
      setTimeout(() => {
        renderBarChart()
        renderRadarChart()
      }, 100)
    })
  } catch (error: any) {
    console.error('Failed to load comparison:', error)
    console.error('Error message:', error.message)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
  } finally {
    loading.value = false
    console.log('Loading complete')
  }
}

onMounted(() => {
  loadDevices()
})

onUnmounted(() => {
  // 清理图表实例
  if (barChart.value) {
    const chart = echarts.getInstanceByDom(barChart.value)
    chart?.dispose()
  }
  if (radarChart.value) {
    const chart = echarts.getInstanceByDom(radarChart.value)
    chart?.dispose()
  }
})
</script>

<style scoped>
.device-compare {
  padding: 20px;
}

.mb-5 {
  margin-bottom: 20px;
}

.mt-5 {
  margin-top: 20px;
}

.device-score-card {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.device-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.total-score {
  font-size: 36px;
  font-weight: bold;
  color: #2080f0;
}

.score-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.chart-container {
  height: 350px;
  width: 100%;
}
</style>
