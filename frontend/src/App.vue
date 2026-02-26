<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout has-sider position="absolute" style="top: 0; bottom: 0">
            <!-- Sidebar -->
            <n-layout-sider
              bordered
              collapse-mode="width"
              :collapsed-width="64"
              :width="240"
              show-trigger
              :native-scrollbar="false"
            >
              <div class="logo">
                <n-icon size="28" color="#2080f0"><Construct /></n-icon>
                <span v-if="!collapsed" class="logo-text">{{ $t('app.title') }}</span>
              </div>
              
              <n-menu
                :collapsed="collapsed"
                :collapsed-width="64"
                :collapsed-icon-size="22"
                :options="menuOptions"
                :value="activeKey"
                @update:value="handleMenuClick"
              />
              
              <!-- Language Switcher -->
              <div class="lang-switch">
                <n-select
                  v-model:value="currentLocale"
                  :options="localeOptions"
                  size="small"
                  style="width: 100px; margin: 8px;"
                />
              </div>
            </n-layout-sider>
            
            <!-- Main Content -->
            <n-layout-content content-style="padding: 16px">
              <router-view />
            </n-layout-content>
          </n-layout>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NConfigProvider, NMessageProvider, NNotificationProvider, NDialogProvider, NLayout, NLayoutSider, NLayoutContent, NMenu, NIcon, NSelect } from 'naive-ui'
import { Construct, Desktop, List, DocumentText, Grid, Settings, BookSharp, BusinessSharp, CodeSlash, PlayCircle, TimeSharp, PieChart } from '@vicons/ionicons5'
import { zhCN, dateZhCN } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const collapsed = ref(false)
const currentLocale = ref('zh-CN')

const activeKey = computed(() => route.name as string)

const themeOverrides = {
  common: {
    primaryColor: '#2080f0',
    primaryColorHover: '#60a5fa',
    primaryColorPressed: '#2563eb'
  }
}

const localeOptions = [
  { label: '中文', value: 'zh-CN' },
  { label: 'English', value: 'en' }
]

// Watch for locale changes
watch(currentLocale, (newLocale) => {
  locale.value = newLocale
})

const renderIcon = (icon: any) => () => h(NIcon, null, { default: () => h(icon) })

const menuOptions = computed(() => [
  {
    label: t('nav.dashboard'),
    key: 'Dashboard',
    icon: renderIcon(Grid)
  },
  {
    label: t('nav.devices'),
    key: 'DeviceList',
    icon: renderIcon(Desktop)
  },
  {
    label: t('nav.tasks'),
    key: 'TaskList',
    icon: renderIcon(List)
  },
  {
    label: t('nav.results'),
    key: 'ResultList',
    icon: renderIcon(DocumentText)
  },
  {
    label: t('nav.standards'),
    key: 'StandardManage',
    icon: renderIcon(Construct)
  },
  {
    label: '测试软件',
    key: 'TestSoftware',
    icon: renderIcon(BookSharp)
  },
  {
    label: '岗位管理',
    key: 'PositionList',
    icon: renderIcon(BusinessSharp)
  },
  {
    label: '软件管理',
    key: 'SoftwareList',
    icon: renderIcon(CodeSlash)
  },
  {
    label: '脚本管理',
    key: 'ScriptList',
    icon: renderIcon(PlayCircle)
  },
  {
    label: '执行记录',
    key: 'ExecutionList',
    icon: renderIcon(TimeSharp)
  },
  {
    label: '设备对比',
    key: 'DeviceCompare',
    icon: renderIcon(PieChart)
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: t('nav.settings'),
    key: 'Settings',
    icon: renderIcon(Settings)
  }
])

const handleMenuClick = (key: string) => {
  router.push({ name: key })
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid #eee;
  font-weight: bold;
  font-size: 16px;
}

.logo-text {
  white-space: nowrap;
}

.lang-switch {
  position: absolute;
  bottom: 0;
  width: 100%;
  padding: 8px;
  border-top: 1px solid #eee;
}
</style>
