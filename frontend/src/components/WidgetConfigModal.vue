<template>
  <n-modal v-model:show="showModal" preset="card" title="看板配置" style="width: 500px;">
    <n-transfer
      v-model:value="selectedWidgets"
      :options="availableWidgets"
      source-title="可用组件"
      target-title="当前看板"
      filterable
    />
    <template #footer>
      <n-button @click="showModal = false">取消</n-button>
      <n-button type="primary" @click="saveConfig">保存</n-button>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NModal, NTransfer, NButton } from 'naive-ui'

const props = defineProps<{
  show: boolean
  active: string[]
}>()

const emit = defineEmits(['update:show', 'save'])

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const availableWidgets = [
  { label: 'CPU 趋势图', value: 'cpu' },
  { label: 'GPU 趋势图', value: 'gpu' },
  { label: '活跃告警', value: 'alerts' }
]

const selectedWidgets = ref<string[]>([])

watch(() => props.active, (newVal) => {
  selectedWidgets.value = [...newVal]
}, { immediate: true })

const saveConfig = () => {
  emit('save', selectedWidgets.value)
  showModal.value = false
}
</script>