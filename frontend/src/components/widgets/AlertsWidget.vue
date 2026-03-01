<template>
  <div class="widget-content">
    <div class="alert-list">
      <div v-for="alert in displayAlerts" :key="alert.id" class="alert-item" :class="alert.severity">
        <div class="alert-header">
          <span class="alert-title">{{ alert.title }}</span>
          <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
        </div>
        <div class="alert-body">{{ alert.message }}</div>
      </div>
      <div v-if="!displayAlerts.length" class="empty-state">
        暂无活跃告警
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: any[]
}>()

const displayAlerts = computed(() => {
  return (props.data || []).slice(0, 5)
})

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleTimeString()
}
</script>

<style scoped>
.widget-content {
  height: 100%;
  overflow-y: auto;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  padding: 8px 12px;
  border-radius: 6px;
  background: #f8fafc;
  border-left: 3px solid #cbd5e1;
}

.alert-item.critical, .alert-item.error {
  background: #fef2f2;
  border-left-color: #ef4444;
}

.alert-item.warning {
  background: #fffbeb;
  border-left-color: #f59e0b;
}

.alert-item.info {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.alert-title {
  font-weight: 500;
  font-size: 13px;
  color: #1e293b;
}

.alert-time {
  font-size: 11px;
  color: #94a3b8;
}

.alert-body {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 20px 0;
  font-size: 13px;
}
</style>