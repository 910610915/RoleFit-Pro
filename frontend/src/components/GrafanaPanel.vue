<template>
  <div class="grafana-panel">
    <div class="panel-header" v-if="title">
      <h3>{{ title }}</h3>
      <n-button size="small" @click="openGrafana">
        <template #icon>
          <n-icon><ExternalLinkOutline /></n-icon>
        </template>
        在 Grafana 中打开
      </n-button>
    </div>
    
    <div class="panel-content">
      <iframe
        v-if="grafanaUrl && isConfigured"
        :src="embeddedUrl"
        :width="width"
        :height="height"
        frameborder="0"
        class="grafana-iframe"
      />
      
      <n-empty v-else-if="!isConfigured" description="Grafana 未配置">
        <template #extra>
          <n-button size="small" @click="openSettings">
            配置 Grafana
          </n-button>
        </template>
      </n-empty>
      
      <n-result v-else status="warning" title="Grafana 不可用" description="请检查 Grafana 服务是否启动">
        <template #footer>
          <n-button size="small" @click="retry">重试</n-button>
        </template>
      </n-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NButton, NIcon, NEmpty, NResult } from 'naive-ui'
import { ExternalLinkOutline } from '@vicons/ionicons5'

const props = defineProps<{
  title?: string
  dashboardUid: string
  panelId?: number
  width?: string | number
  height?: string | number
  deviceId?: string
  timeFrom?: string
  timeTo?: string
}>()

const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000'
const isConfigured = ref(true)

const embeddedUrl = computed(() => {
  if (!grafanaUrl) return ''
  
  const base = `${grafanaUrl}/d-solo/${props.dashboardUid}`
  const params = new URLSearchParams()
  
  if (props.panelId) params.append('panelId', String(props.panelId))
  if (props.deviceId) params.append('var-instance', props.deviceId)
  params.append('from', props.timeFrom || 'now-1h')
  params.append('to', props.timeTo || 'now')
  params.append('theme', 'light')
  
  return `${base}?${params.toString()}`
})

const openGrafana = () => {
  window.open(`${grafanaUrl}/d/${props.dashboardUid}`, '_blank')
}

const openSettings = () => {
  // Navigate to settings page for Grafana configuration
  console.log('Open Grafana settings')
}

const retry = () => {
  isConfigured.value = true
}
</script>

<style scoped>
.grafana-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.panel-content {
  min-height: 100px;
}

.grafana-iframe {
  border-radius: 4px;
  width: 100%;
}
</style>
