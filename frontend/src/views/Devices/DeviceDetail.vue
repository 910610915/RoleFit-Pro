<template>
  <div class="device-detail">
    <n-button @click="router.back()" class="back-btn">
      <template #icon><n-icon><arrow-back /></n-icon></template>
      返回
    </n-button>
    
    <n-spin :show="loading">
      <n-grid :cols="2" :x-gap="20" :y-gap="20">
        <!-- Device Info -->
        <n-gi>
          <n-card title="设备信息">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="状态">
                <n-tag :type="device.status === 'online' ? 'success' : 'default'">{{ device.status === 'online' ? '在线' : device.status === 'offline' ? '离线' : device.status === 'testing' ? '测试中' : device.status }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="设备名称">{{ device.device_name }}</n-descriptions-item>
              <n-descriptions-item label="MAC地址">{{ device.mac_address }}</n-descriptions-item>
              <n-descriptions-item label="IP地址">{{ device.ip_address }}</n-descriptions-item>
              <n-descriptions-item label="主机名">{{ device.hostname }}</n-descriptions-item>
              <n-descriptions-item label="部门">{{ device.department }}</n-descriptions-item>
              <n-descriptions-item label="岗位">{{ device.position }}</n-descriptions-item>
              <n-descriptions-item label="分配给">{{ device.assigned_to }}</n-descriptions-item>
              <n-descriptions-item label="最后在线">{{ device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : '-' }}</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
        
        <!-- Hardware Info -->
        <n-gi>
          <n-card title="硬件信息">
            <n-tabs type="line">
              <n-tab-pane name="cpu" tab="处理器">
                <n-descriptions :column="1" label-placement="left">
                  <n-descriptions-item label="型号">{{ device.cpu_model || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="核心数">{{ device.cpu_cores || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="线程数">{{ device.cpu_threads || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="基础频率">{{ device.cpu_base_clock ? device.cpu_base_clock + ' GHz' : '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-tab-pane>
              <n-tab-pane name="gpu" tab="显卡">
                <n-space vertical>
                  <n-card v-if="device.all_gpus && device.all_gpus.length > 0" v-for="(gpu, index) in device.all_gpus" :key="index" size="small">
                    <n-descriptions :column="2" label-placement="left">
                      <n-descriptions-item label="显卡">{{ gpu.name || '-' }}</n-descriptions-item>
                      <n-descriptions-item label="显存">{{ gpu.vram_mb ? gpu.vram_mb + ' MB' : '-' }}</n-descriptions-item>
                      <n-descriptions-item label="驱动版本">{{ gpu.driver_version || '-' }}</n-descriptions-item>
                    </n-descriptions>
                  </n-card>
                  <n-empty v-else-if="!device.gpu_model" description="暂无显卡信息" />
                  <n-descriptions v-else :column="1" label-placement="left">
                    <n-descriptions-item label="型号">{{ device.gpu_model || '-' }}</n-descriptions-item>
                    <n-descriptions-item label="显存">{{ device.gpu_vram_mb ? device.gpu_vram_mb + ' MB' : '-' }}</n-descriptions-item>
                    <n-descriptions-item label="驱动版本">{{ device.gpu_driver_version || '-' }}</n-descriptions-item>
                  </n-descriptions>
                </n-space>
              </n-tab-pane>
              <n-tab-pane name="memory" tab="内存">
                <n-space vertical>
                  <n-card v-if="device.all_memory && device.all_memory.length > 0" v-for="(mem, index) in device.all_memory" :key="index" size="small">
                    <n-descriptions :column="2" label-placement="left">
                      <n-descriptions-item label="槽位{{ index + 1 }}">{{ mem.capacity_mb ? (mem.capacity_mb / 1024).toFixed(0) + ' GB' : '-' }}</n-descriptions-item>
                      <n-descriptions-item label="频率">{{ mem.speed ? mem.speed + ' MHz' : '-' }}</n-descriptions-item>
                    </n-descriptions>
                  </n-card>
                  <n-descriptions v-if="!device.all_memory || device.all_memory.length === 0" :column="1" label-placement="left">
                    <n-descriptions-item label="总容量">{{ device.ram_total_gb ? device.ram_total_gb + ' GB' : '-' }}</n-descriptions-item>
                    <n-descriptions-item label="频率">{{ device.ram_frequency ? device.ram_frequency + ' MHz' : '-' }}</n-descriptions-item>
                  </n-descriptions>
                </n-space>
              </n-tab-pane>
              <n-tab-pane name="storage" tab="存储">
                <n-space vertical>
                  <n-card v-if="device.all_disks && device.all_disks.length > 0" v-for="(disk, index) in device.all_disks" :key="index" size="small">
                    <n-descriptions :column="2" label-placement="left">
                      <n-descriptions-item label="磁盘{{ index + 1 }}">{{ disk.model || '-' }}</n-descriptions-item>
                      <n-descriptions-item label="容量">{{ disk.capacity_tb ? disk.capacity_tb + ' TB' : '-' }}</n-descriptions-item>
                      <n-descriptions-item label="类型">{{ disk.type || '-' }}</n-descriptions-item>
                    </n-descriptions>
                  </n-card>
                  <n-empty v-else-if="!device.disk_model" description="暂无磁盘信息" />
                  <n-descriptions v-else :column="1" label-placement="left">
                    <n-descriptions-item label="型号">{{ device.disk_model || '-' }}</n-descriptions-item>
                    <n-descriptions-item label="容量">{{ device.disk_capacity_tb ? device.disk_capacity_tb + ' TB' : '-' }}</n-descriptions-item>
                    <n-descriptions-item label="类型">{{ device.disk_type || '-' }}</n-descriptions-item>
                  </n-descriptions>
                </n-space>
              </n-tab-pane>
              <n-tab-pane name="os" tab="操作系统">
                <n-descriptions :column="1" label-placement="left">
                  <n-descriptions-item label="名称">{{ device.os_name || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="版本">{{ device.os_version || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="构建号">{{ device.os_build || '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-tab-pane>
            </n-tabs>
          </n-card>
        </n-gi>
      </n-grid>
      
      <!-- Performance Summary -->
      <n-card title="性能概览" class="perf-card">
        <n-grid :cols="4" :x-gap="20">
          <n-gi>
            <div class="score-item">
              <div class="score-value">{{ perfStats.latest_score?.toFixed(1) || '-' }}</div>
              <div class="score-label">最新分数</div>
            </div>
          </n-gi>
          <n-gi>
            <div class="score-item">
              <div class="score-value">{{ perfStats.average_score?.toFixed(1) || '-' }}</div>
              <div class="score-label">平均分数</div>
            </div>
          </n-gi>
          <n-gi>
            <div class="score-item">
              <div class="score-value">{{ perfStats.total_tests }}</div>
              <div class="score-label">测试总数</div>
            </div>
          </n-gi>
          <n-gi>
            <div class="score-item">
              <div class="score-value" :class="perfStats.trend">{{ perfStats.trend === 'improving' ? '上升' : perfStats.trend === 'declining' ? '下降' : '-' }}</div>
              <div class="score-label">趋势</div>
            </div>
          </n-gi>
        </n-grid>
      </n-card>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NCard, NGrid, NGi, NDescriptions, NDescriptionsItem, NTag, NIcon, NTabs, NTabPane, NSpin } from 'naive-ui'
import { ArrowBack } from '@vicons/ionicons5'
import { deviceApi, type Device } from '@/api/devices'
import { resultApi } from '@/api/results'

const route = useRoute()
const router = useRouter()

const deviceId = route.params.id as string
const loading = ref(false)

const device = reactive<Device>({
  id: '',
  device_name: '',
  mac_address: '',
  status: 'offline',
  registered_at: ''
})

const perfStats = reactive({
  latest_score: null as number | null,
  average_score: null as number | null,
  total_tests: 0,
  trend: ''
})

const loadDevice = async () => {
  loading.value = true
  try {
    const res = await deviceApi.get(deviceId)
    Object.assign(device, res.data)
    
    // Load performance stats
    const statsRes = await resultApi.getDeviceStats(deviceId)
    Object.assign(perfStats, statsRes.data)
  } catch (error) {
    console.error('Failed to load device:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDevice()
})
</script>

<style scoped>
.device-detail {
  padding: 20px;
}

.back-btn {
  margin-bottom: 20px;
}

.perf-card {
  margin-top: 20px;
}

.score-item {
  text-align: center;
  padding: 20px;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.score-value.improving { color: #18a058; }
.score-value.declining { color: #d03050; }

.score-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}
</style>
