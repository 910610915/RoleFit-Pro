<template>
  <div class="settings-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <n-icon size="28" color="#0ea5e9"><Settings /></n-icon>
        <n-h1 class="title">系统设置</n-h1>
      </div>
    </div>
    
    <!-- Content -->
    <div class="settings-content">
      <n-tabs type="line" class="settings-tabs">
        <n-tab-pane name="general" tab="常规设置">
          <n-card class="settings-card">
            <n-form label-placement="left" label-width="120px">
              <n-form-item label="API地址">
                <n-input v-model:value="settings.api_base_url" placeholder="http://localhost:8000/api" />
              </n-form-item>
              <n-form-item label="数据刷新间隔">
                <n-input-number v-model:value="settings.refresh_interval" :min="5" :max="300" />
                <span class="unit-text">秒</span>
              </n-form-item>
              <n-form-item>
                <n-button type="primary" class="save-btn" @click="saveSettings">保存设置</n-button>
              </n-form-item>
            </n-form>
          </n-card>
        </n-tab-pane>
        
        <n-tab-pane name="notifications" tab="通知设置">
          <n-card class="settings-card">
            <n-space vertical>
              <n-checkbox v-model:checked="settings.notify_on_task_complete">任务完成时通知</n-checkbox>
              <n-checkbox v-model:checked="settings.notify_on_device_offline">设备离线时通知</n-checkbox>
              <n-checkbox v-model:checked="settings.notify_on_standard_fail">标准检查失败时通知</n-checkbox>
              <n-button type="primary" class="save-btn" style="margin-top: 16px" @click="saveSettings">保存设置</n-button>
            </n-space>
          </n-card>
        </n-tab-pane>
        
        <n-tab-pane name="about" tab="关于系统">
          <n-card class="settings-card">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="版本">1.0.0</n-descriptions-item>
              <n-descriptions-item label="构建日期">2026-02-23</n-descriptions-item>
              <n-descriptions-item label="系统">硬件性能基准测试与岗位配置分析系统</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="help" tab="测试说明">
          <n-card class="settings-card" title="测试类型说明">
            <n-space vertical>
              <n-collapse>
                <n-collapse-item title="性能测试 (benchmark)" name="benchmark">
                  <n-space vertical>
                    <n-text>快速测试设备的基础性能指标，适合日常巡检。</n-text>
                    <n-space>
                      <n-tag type="info">预计时长: 5-10分钟</n-tag>
                    </n-space>
                    <n-text depth="3">测试项目: CPU跑分、GPU跑分、内存读写、磁盘读写</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="模拟测试 (simulation)" name="simulation">
                  <n-space vertical>
                    <n-text>模拟游戏开发工作负载，测试设备在实际游戏开发场景下的表现。</n-text>
                    <n-space>
                      <n-tag type="info">预计时长: 15-20分钟</n-tag>
                    </n-space>
                    <n-text depth="3">测试项目: CPU多核渲染、GPU图形渲染、内存压力测试、磁盘IO</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="完整测试 (full)" name="full">
                  <n-space vertical>
                    <n-text>全面的硬件性能测试，包含所有测试项目，生成详细的性能报告。</n-text>
                    <n-space>
                      <n-tag type="info">预计时长: 30-60分钟</n-tag>
                    </n-space>
                    <n-text depth="3">测试项目: CPU基准测试、GPU基准测试、内存压力测试、磁盘基准测试、综合评分</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="自定义测试 (custom)" name="custom">
                  <n-space vertical>
                    <n-text>灵活自定义测试项目，可选择需要测试的硬件组件和参数。</n-text>
                    <n-space>
                      <n-tag type="info">预计时长: 根据选择项目</n-tag>
                    </n-space>
                    <n-text depth="3">可配置: CPU/GPU/内存/磁盘、测试时长、采样间隔</n-text>
                  </n-space>
                </n-collapse-item>
              </n-collapse>
            </n-space>
          </n-card>

          <n-card class="settings-card" title="Agent测试软件要求" style="margin-top: 16px">
            <n-space vertical>
              <n-alert type="info" style="margin-bottom: 16px">
                以下软件用于在实际设备上执行真实的性能测试。当前版本为模拟测试，如需真实测试请安装相应软件。
              </n-alert>

              <n-collapse>
                <n-collapse-item title="CPU测试" name="cpu">
                  <n-space vertical>
                    <n-text>推荐软件: GeekBench, Cinebench, sysbench, Prime95</n-text>
                    <n-text depth="3">测试CPU的单核和多核性能、整数/浮点运算能力</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="GPU测试" name="gpu">
                  <n-space vertical>
                    <n-text>推荐软件: FurMark, 3DMark, Unigine Superposition, Heaven</n-text>
                    <n-text depth="3">测试GPU的图形渲染性能、DirectX/OpenGL性能</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="内存测试" name="memory">
                  <n-space vertical>
                    <n-text>推荐软件: AIDA64, MemTest86, TestMem5</n-text>
                    <n-text depth="3">测试内存读写速度、延迟、稳定性</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="磁盘测试" name="disk">
                  <n-space vertical>
                    <n-text>推荐软件: CrystalDiskMark, AS SSD Benchmark, ATTO</n-text>
                    <n-text depth="3">测试磁盘读写速度、4K随机读写、IOPS</n-text>
                  </n-space>
                </n-collapse-item>
              </n-collapse>
            </n-space>
          </n-card>
        </n-tab-pane>
      </n-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { NH1, NTabs, NTabPane, NCard, NForm, NFormItem, NInput, NInputNumber, NButton, NCheckbox, NSpace, NDescriptions, NDescriptionsItem, NCollapse, NCollapseItem, NText, NAlert, NTag, NIcon } from 'naive-ui'
import { Settings } from '@vicons/ionicons5'

const settings = reactive({
  api_base_url: import.meta.env.VITE_API_BASE_URL || '/api',
  refresh_interval: 30,
  notify_on_task_complete: true,
  notify_on_device_offline: true,
  notify_on_standard_fail: true
})

const saveSettings = () => {
  localStorage.setItem('settings', JSON.stringify(settings))
  alert('设置已保存！')
}
</script>

<style scoped>
.settings-page {
  padding: 0;
  min-height: 100%;
  background: #f8fafc;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title .title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
}

/* Content */
.settings-content {
  padding: 24px;
}

.settings-tabs {
  background: transparent;
}

.settings-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.settings-card :deep(.n-card__content) {
  padding: 20px;
}

.unit-text {
  margin-left: 8px;
  color: #64748b;
}

.save-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}

.save-btn:hover {
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
  transform: translateY(-1px);
}
</style>
