<template>
  <div class="widget-content">
    <div ref="chartRef" style="height: 150px; width: 100%;"></div>
    <div class="widget-stats">
      <div class="stat-item">
        <span class="label">当前</span>
        <span class="value">{{ current.toFixed(1) }}%</span>
      </div>
      <div class="stat-item">
        <span class="label">峰值</span>
        <span class="value">{{ peak.toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: number[]
  title?: string
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
const current = ref(0)
const peak = ref(0)

const initChart = () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    updateChart()
  }
}

const updateChart = () => {
  if (!chart) return
  
  const data = props.data || []
  current.value = data.length > 0 ? data[data.length - 1] : 0
  peak.value = data.length > 0 ? Math.max(...data) : 0
  
  chart.setOption({
    grid: { left: 0, right: 0, top: 10, bottom: 0 },
    xAxis: { show: false, type: 'category', data: data.map((_, i) => i) },
    yAxis: { show: false, type: 'value', max: 100 },
    series: [{
      type: 'line',
      smooth: true,
      showSymbol: false,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
        ])
      },
      lineStyle: { color: '#3b82f6', width: 2 },
      data: data
    }]
  })
}

watch(() => props.data, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => chart?.resize())
  chart?.dispose()
})
</script>

<style scoped>
.widget-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.widget-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}
.stat-item {
  display: flex;
  gap: 4px;
}
.value {
  font-weight: 600;
  color: #1e293b;
}
</style>