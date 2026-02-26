<template>
  <div class="dashboard-page">
    <!-- Particle Background -->
    <ParticleBackgroundWhite />
    
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-left">
        <h1 class="logo">RoleFit Pro</h1>
        <span class="subtitle">智能硬件性能基准测试平台</span>
      </div>
      <div class="header-right">
        <n-button text @click="$router.push('/system')">
          <template #icon>
            <n-icon><Settings /></n-icon>
          </template>
          系统管理
        </n-button>
      </div>
    </header>
    
    <!-- Main Content -->
    <div class="dashboard-content">
      <!-- Stats Section -->
      <section class="stats-section">
        <div class="stat-card" v-for="(stat, index) in stats" :key="index">
          <div class="stat-icon">
            <n-icon size="32" :color="stat.color">
              <component :is="stat.icon" />
            </n-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </section>
      
      <!-- Feature Cards Grid -->
      <section class="feature-section">
        <h2 class="section-title">功能导航</h2>
        <div class="feature-grid">
          <div 
            class="feature-card" 
            v-for="card in visibleCards" 
            :key="card.id"
            @click="navigateTo(card.route)"
          >
            <div class="card-icon">
              <n-icon size="48">
                <component :is="getIcon(card.icon)" />
              </n-icon>
            </div>
            <div class="card-content">
              <h3>{{ card.title }}</h3>
              <p>{{ card.description }}</p>
            </div>
            <div class="card-arrow">
              <n-icon size="20"><ArrowForward /></n-icon>
            </div>
          </div>
        </div>
      </section>
      
      <!-- Quick Charts -->
      <section class="charts-section">
        <div class="chart-card">
          <h3>设备状态分布</h3>
          <div ref="statusChartRef" style="height: 280px;"></div>
        </div>
        <div class="chart-card">
          <h3>性能评分趋势</h3>
          <div ref="trendChartRef" style="height: 280px;"></div>
        </div>
      </section>
    </div>
    
    <!-- User Info Bottom Left -->
    <div class="user-info-bar">
      <div class="user-avatar">
        <n-icon size="24"><PersonCircle /></n-icon>
      </div>
      <div class="user-details">
        <span class="username">{{ currentUser?.username || '用户' }}</span>
        <span class="role">{{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}</span>
      </div>
      <n-button size="small" quaternary @click="handleLogout">
        <template #icon>
          <n-icon><LogOut /></n-icon>
        </template>
        退出
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NIcon, useMessage } from 'naive-ui'
import ParticleBackgroundWhite from '@/components/ParticleBackgroundWhite.vue'
import { featureCardApi, type FeatureCard } from '@/api/featureCards'
import { statsApi } from '@/api/stats'
import * as echarts from 'echarts'
import {
  Desktop,
  People,
  Apps,
  Code,
  List,
  Play,
  GitCompare,
  StatsChart,
  Settings,
  ArrowForward,
  PersonCircle,
  LogOut,
  Ribbon,
  TrendingUp,
  CheckmarkCircle,
  CloseCircle
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

// Feature cards
const featureCards = ref<FeatureCard[]>([])
const visibleCards = computed(() => 
  featureCards.value.filter(c => c.is_visible).sort((a, b) => a.sort_order - b.sort_order)
)

// Stats
const stats = ref([
  { icon: Desktop, value: 0, label: '设备总数', color: '#2080f0' },
  { icon: List, value: 0, label: '任务总数', color: '#18a058' },
  { icon: CheckmarkCircle, value: 0, label: '通过测试', color: '#f0a020' },
  { icon: TrendingUp, value: 0, label: '平均分数', color: '#9c27b0' },
])

// Current user
const currentUser = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

// Chart refs
const statusChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()

// Icon mapping
const getIcon = (iconName?: string) => {
  const icons: Record<string, any> = {
    'desktop': Desktop,
    'people': People,
    'apps': Apps,
    'code': Code,
    'list': List,
    'play': Play,
    'git-compare': GitCompare,
    'stats': StatsChart,
    'settings': Settings,
  }
  return icons[iconName || 'apps'] || Apps
}

// Load data
const loadData = async () => {
  try {
    // Load feature cards
    const cardsRes = await featureCardApi.list()
    featureCards.value = cardsRes.data.items
    
    // Load stats
    const statsRes = await statsApi.getDashboard()
    const data = statsRes.data
    
    stats.value = [
      { icon: Desktop, value: data.total_devices, label: '设备总数', color: '#2080f0' },
      { icon: List, value: data.total_tasks, label: '任务总数', color: '#18a058' },
      { icon: CheckmarkCircle, value: data.passed_tests, label: '通过测试', color: '#f0a020' },
      { icon: TrendingUp, value: Number(data.average_score?.toFixed(1)) || 0, label: '平均分数', color: '#9c27b0' },
    ]
    
    // Load charts
    initCharts()
  } catch (error) {
    console.error('Failed to load data:', error)
  }
}

const initCharts = async () => {
  try {
    // Device status
    const statusRes = await statsApi.getDeviceStatusDistribution()
    const statusData = statusRes.data
    
    if (statusChartRef.value) {
      const chart = echarts.init(statusChartRef.value)
      chart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          data: [
            { value: statusData.online || 0, name: '在线', itemStyle: { color: '#18a058' } },
            { value: statusData.offline || 0, name: '离线', itemStyle: { color: '#8c8c8c' } },
            { value: statusData.testing || 0, name: '测试中', itemStyle: { color: '#f0a020' } },
          ].filter(d => d.value > 0)
        }]
      })
    }
    
    // Score trend
    const trendRes = await statsApi.getScoreTrend(30)
    const trendData = trendRes.data
    
    if (trendChartRef.value) {
      const chart = echarts.init(trendChartRef.value)
      chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { top: 20, right: 20, bottom: 30, left: 40 },
        xAxis: { 
          type: 'category', 
          data: trendData.map(d => d.date.slice(5)),
          axisLine: { lineStyle: { color: '#e0e0e0' } }
        },
        yAxis: { 
          type: 'value', 
          min: 0, 
          max: 100,
          axisLine: { lineStyle: { color: '#e0e0e0' } },
          splitLine: { lineStyle: { color: '#f0f0f0' } }
        },
        series: [{
          type: 'line',
          data: trendData.map(d => d.average_score),
          smooth: true,
          areaStyle: { opacity: 0.2, color: '#2080f0' },
          itemStyle: { color: '#2080f0' },
          lineStyle: { width: 2 }
        }]
      })
    }
  } catch (error) {
    console.error('Failed to load charts:', error)
  }
}

// Navigation
const navigateTo = (route?: string) => {
  if (route) {
    router.push(route)
  }
}

// Logout
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  message.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dashboard-page {
  position: relative;
  min-height: 100vh;
  background: #fff;
}

.dashboard-header {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #f0f0f0;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .logo {
      font-size: 24px;
      font-weight: 700;
      color: #000;
      margin: 0;
    }
    
    .subtitle {
      font-size: 14px;
      color: #666;
    }
  }
}

.dashboard-content {
  position: relative;
  z-index: 5;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

// Stats Section
.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 48px;
}

.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }
  
  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .stat-info {
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: #000;
      line-height: 1.2;
    }
    
    .stat-label {
      font-size: 14px;
      color: #666;
      margin-top: 4px;
    }
  }
}

// Feature Section
.feature-section {
  margin-bottom: 48px;
  
  .section-title {
    font-size: 20px;
    font-weight: 600;
    color: #000;
    margin-bottom: 24px;
  }
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.feature-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    
    .card-arrow {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .card-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
    flex-shrink: 0;
  }
  
  .card-content {
    flex: 1;
    min-width: 0;
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #000;
      margin: 0 0 6px 0;
    }
    
    p {
      font-size: 13px;
      color: #666;
      margin: 0;
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  
  .card-arrow {
    position: absolute;
    right: 20px;
    color: #999;
    opacity: 0;
    transform: translateX(-10px);
    transition: all 0.3s ease;
  }
}

// Charts Section
.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  
  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #000;
    margin: 0 0 16px 0;
  }
}

// User Info Bar (Bottom Left)
.user-info-bar {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 12px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  
  .user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
  }
  
  .user-details {
    display: flex;
    flex-direction: column;
    
    .username {
      font-size: 14px;
      font-weight: 600;
      color: #000;
    }
    
    .role {
      font-size: 12px;
      color: #666;
    }
  }
}

// Responsive
@media (max-width: 1200px) {
  .feature-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .stats-section,
  .feature-grid,
  .charts-section {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
