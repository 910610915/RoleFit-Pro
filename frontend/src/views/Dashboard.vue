<template>
  <div class="dashboard">
    <n-h1>{{ $t('dashboard.title') }}</n-h1>
    
    <!-- Summary Cards -->
    <n-grid :cols="4" :x-gap="20" :y-gap="20" class="summary-grid">
      <n-gi>
        <n-card class="stat-card">
          <div class="stat-content">
            <n-icon size="40" color="#2080f0">
              <desktop />
            </n-icon>
            <div class="stat-info">
              <div class="stat-value">{{ summary.total_devices }}</div>
              <div class="stat-label">{{ $t('dashboard.totalDevices') }}</div>
            </div>
          </div>
          <div class="stat-detail">
            <span class="online">{{ summary.online_devices }} {{ $t('dashboard.online') }}</span>
            <span class="offline">{{ summary.offline_devices }} {{ $t('dashboard.offline') }}</span>
          </div>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <div class="stat-content">
            <n-icon size="40" color="#18a058">
              <list />
            </n-icon>
            <div class="stat-info">
              <div class="stat-value">{{ summary.total_tasks }}</div>
              <div class="stat-label">{{ $t('dashboard.totalTasks') }}</div>
            </div>
          </div>
          <div class="stat-detail">
            <span class="pending">{{ summary.pending_tasks }} {{ $t('dashboard.pending') }}</span>
            <span class="running">{{ summary.running_tasks }} {{ $t('dashboard.running') }}</span>
          </div>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <div class="stat-content">
            <n-icon size="40" color="#f0a020">
              <stats-chart />
            </n-icon>
            <div class="stat-info">
              <div class="stat-value">{{ summary.total_tests }}</div>
              <div class="stat-label">{{ $t('dashboard.totalTests') }}</div>
            </div>
          </div>
          <div class="stat-detail">
            <span class="passed">{{ summary.passed_tests }} {{ $t('dashboard.passed') }}</span>
            <span class="failed">{{ summary.failed_tests }} {{ $t('dashboard.failed') }}</span>
          </div>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <div class="stat-content">
            <n-icon size="40" color="#9c27b0">
              <ribbon />
            </n-icon>
            <div class="stat-info">
              <div class="stat-value">{{ summary.average_score.toFixed(1) }}</div>
              <div class="stat-label">{{ $t('dashboard.averageScore') }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
    
    <!-- Charts Row -->
    <n-grid :cols="2" :x-gap="20" :y-gap="20" class="charts-grid">
      <n-gi>
        <n-card :title="$t('dashboard.deviceStatus')">
          <div ref="statusChartRef" style="height: 300px;"></div>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card :title="$t('dashboard.scoreTrend')">
          <div ref="trendChartRef" style="height: 300px;"></div>
        </n-card>
      </n-gi>
    </n-grid>
    
    <!-- Department Table -->
    <n-card :title="$t('dashboard.devicesByDept')" class="dept-card">
      <n-data-table
        :columns="deptColumns"
        :data="departments"
        :bordered="false"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NCard, NGrid, NGi, NH1, NIcon, NDataTable, NProgress, NSpace, NTag } from 'naive-ui'
import { Desktop, List, StatsChart, Ribbon } from '@vicons/ionicons5'
import * as echarts from 'echarts'
import { statsApi, type DashboardSummary, type DepartmentDeviceCount, type ScoreTrend } from '@/api/stats'

const { t } = useI18n()

const summary = ref<DashboardSummary>({
  total_devices: 0,
  online_devices: 0,
  offline_devices: 0,
  testing_devices: 0,
  total_tasks: 0,
  pending_tasks: 0,
  running_tasks: 0,
  completed_tasks: 0,
  total_tests: 0,
  passed_tests: 0,
  failed_tests: 0,
  average_score: 0
})

const departments = ref<DepartmentDeviceCount[]>([])
const scoreTrend = ref<ScoreTrend[]>([])

const statusChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()

const deptColumns = computed(() => [
  { title: t('dashboard.department'), key: 'department' },
  { title: t('dashboard.deviceCount'), key: 'count' },
  { title: t('dashboard.online'), key: 'online_count' },
  { 
    title: t('dashboard.avgScore'), 
    key: 'average_score',
    render: (row: DepartmentDeviceCount) => row.average_score?.toFixed(1) || '-'
  }
])

const loadDashboard = async () => {
  try {
    const [dashRes, deptRes, trendRes] = await Promise.all([
      statsApi.getDashboard(),
      statsApi.getDevicesByDepartment(),
      statsApi.getScoreTrend(30)
    ])
    
    summary.value = dashRes.data
    departments.value = deptRes.data
    scoreTrend.value = trendRes.data
    
    initCharts()
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

const initCharts = () => {
  // Status Pie Chart
  if (statusChartRef.value) {
    const chart = echarts.init(statusChartRef.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: summary.value.online_devices, name: 'Online', itemStyle: { color: '#18a058' } },
          { value: summary.value.offline_devices, name: 'Offline', itemStyle: { color: '#8c8c8c' } },
          { value: summary.value.testing_devices, name: 'Testing', itemStyle: { color: '#f0a020' } },
          { value: summary.value.testing_devices, name: 'Error', itemStyle: { color: '#d03050' } }
        ].filter(d => d.value > 0)
      }]
    })
  }
  
  // Trend Line Chart
  if (trendChartRef.value) {
    const chart = echarts.init(trendChartRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { 
        type: 'category', 
        data: scoreTrend.value.map(d => d.date.slice(5)) 
      },
      yAxis: { type: 'value', min: 0, max: 100 },
      series: [{
        type: 'line',
        data: scoreTrend.value.map(d => d.average_score),
        smooth: true,
        areaStyle: { opacity: 0.3 },
        itemStyle: { color: '#2080f0' }
      }]
    })
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.summary-grid {
  margin-bottom: 20px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-detail {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 16px;
  font-size: 12px;
}

.stat-detail .online { color: #18a058; }
.stat-detail .offline { color: #8c8c8c; }
.stat-detail .pending { color: #f0a020; }
.stat-detail .running { color: #2080f0; }
.stat-detail .passed { color: #18a058; }
.stat-detail .failed { color: #d03050; }

.charts-grid {
  margin-bottom: 20px;
}

.dept-card {
  margin-top: 20px;
}
</style>
