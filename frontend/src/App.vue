<template>
  <!-- Global Cursor Effect -->
  <SleekLineCursor :trails="20" :size="50" />
  
  <!-- Aurora Background -->
  <AuroraBackground class="aurora-bg">
  
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <!-- 登录页面不显示侧边栏 -->
          <template v-if="route.name === 'Login'">
            <router-view />
          </template>
          
          <!-- 其他页面显示侧边栏布局 -->
          <template v-else>
            <n-layout has-sider position="absolute" style="top: 0; bottom: 0">
              <!-- Sidebar - Redesigned with UI/UX Pro Max -->
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed-width="72"
                :width="260"
                show-trigger
                style="z-index: 10; background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);"
              >
                <!-- Logo Section -->
                <div class="sidebar-logo">
                  <div class="logo-icon">
                    <n-icon size="24" color="#fff">
                      <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="14" stroke-linecap="round">
                        <g transform="rotate(45 50 50)">
                          <line x1="25" y1="20" x2="25" y2="35" /> 
                          <line x1="25" y1="55" x2="25" y2="85" />
                          <line x1="50" y1="15" x2="50" y2="55" />
                          <line x1="50" y1="75" x2="50" y2="85" />
                          <line x1="75" y1="15" x2="75" y2="15" />
                          <line x1="75" y1="35" x2="75" y2="70" />
                          <line x1="75" y1="90" x2="75" y2="90" />
                        </g>
                      </svg>
                    </n-icon>
                  </div>
                  <span v-if="!collapsed" class="logo-text">RoleFit Pro</span>
                </div>
                
                <!-- Menu -->
                <n-menu
                  :collapsed="collapsed"
                  :collapsed-width="72"
                  :collapsed-icon-size="22"
                  :options="menuOptions"
                  :value="activeKey"
                  @update:value="handleMenuClick"
                  class="sidebar-menu"
                />
                
                <!-- Bottom Section - User Info & Logout -->
                <div class="sidebar-footer">
                  <div class="user-card" v-if="!collapsed">
                    <div class="user-avatar">
                      <n-icon size="20"><PersonCircle /></n-icon>
                    </div>
                    <div class="user-info">
                      <span class="username">{{ currentUser?.username || '用户' }}</span>
                      <span class="role">{{ currentUser?.role === 'admin' ? '管理员' : '普通用户' }}</span>
                    </div>
                  </div>
                  <n-button 
                    class="logout-btn" 
                    quaternary 
                    size="small"
                    :collapsed-icon-size="20"
                    @click="handleLogout"
                  >
                    <template #icon>
                      <n-icon><LogOutOutline /></n-icon>
                    </template>
                    <span v-if="!collapsed">退出登录</span>
                  </n-button>
                </div>
              </n-layout-sider>
               
              <n-layout-content style="padding: 0;">
                <router-view />
              </n-layout-content>
            </n-layout>
            
            <!-- Floating AI Chat Button (Chrome extension style) -->
            <div class="ai-float-btn" @click="showAiDrawer = true" title="AI 助手">
              <n-icon size="28"><HardwareChip /></n-icon>
            </div>
            
            <!-- AI Chat Drawer -->
            <n-drawer
              v-model:show="showAiDrawer"
              :width="420"
              placement="right"
              :trap-focus="true"
              :block-scroll="false"
            >
              <n-drawer-content title="AI 助手" closable>
                <AIChatDrawer />
              </n-drawer-content>
            </n-drawer>
          </template>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
  </AuroraBackground>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NConfigProvider, NMessageProvider, NNotificationProvider, NDialogProvider, NLayout, NLayoutSider, NLayoutContent, NMenu, NIcon, NSelect, NLayoutFooter, NButton, NDrawer, NDrawerContent } from 'naive-ui'
import { Construct, Desktop, List, DocumentText, Grid, Settings, BookSharp, BusinessSharp, CodeSlash, PlayCircle, TimeSharp, PieChart, PersonCircle, LogOutOutline, HardwareChip } from '@vicons/ionicons5'
import { zhCN, dateZhCN } from 'naive-ui'
import AIChatDrawer from './components/AIChatDrawer.vue'
import SleekLineCursor from './components/ui/sleek-line-cursor/SleekLineCursor.vue'
import AuroraBackground from './components/ui/aurora-background/AuroraBackground.vue'

const router = useRouter()
const route = useRoute()
const { t, locale } = useI18n()
const collapsed = ref(false)
const currentLocale = ref('zh-CN')
const showAiDrawer = ref(false)

// Current user from localStorage
const currentUser = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

// Logout function
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

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
    icon: renderIcon(CodeSlash)
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
  },
  {
    label: '系统管理',
    key: 'system',
    icon: renderIcon(Settings)
  }
])

const handleMenuClick = (key: string) => {
  router.push({ name: key })
}
</script>

<style>
/* Base Reset */
body {
  margin: 0;
  padding: 0;
}

/* Sidebar Logo */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  padding: 0 16px;
}

.sidebar-logo .logo-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-logo .logo-text {
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.3px;
}

/* Sidebar Menu Customization */
.sidebar-menu {
  padding: 12px 8px;
}

.sidebar-menu :deep(.n-menu-item) {
  border-radius: 10px;
  margin-bottom: 4px;
}

.sidebar-menu :deep(.n-menu-item:hover) {
  background: rgba(14, 165, 233, 0.08);
}

.sidebar-menu :deep(.n-menu-item--selected) {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(2, 132, 199, 0.1) 100%);
}

.sidebar-menu :deep(.n-menu-item--selected .n-menu-item-content::after) {
  display: none;
}

/* Sidebar Footer - User Card */
.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  border-top: 1px solid #e2e8f0;
  background: #fff;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
}

.user-card .user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.user-card .user-info {
  display: flex;
  flex-direction: column;
}

.user-card .username {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
}

.user-card .role {
  font-size: 12px;
  color: #64748b;
}

/* Logout Button */
.logout-btn {
  width: 100%;
  justify-content: center;
  border-radius: 10px;
  color: #ef4444;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.08);
}

/* Legacy styles for compatibility */
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

/* User Info Bar - Bottom Left (Legacy - kept for Dashboard compatibility) */
.user-info-bar {
  position: fixed;
  bottom: 16px;
  left: 16px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 10px 16px;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #eee;
}

.user-info-bar .user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.user-info-bar .user-details {
  display: flex;
  flex-direction: column;
}

.user-info-bar .username {
  font-size: 13px;
  font-weight: 600;
  color: #000;
  line-height: 1.2;
}

.user-info-bar .role {
  font-size: 11px;
  color: #888;
}

/* Floating AI Chat Button */
.ai-float-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  z-index: 9999;
  transition: all 0.3s ease;
}

.ai-float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
}

.ai-float-btn:active {
  transform: scale(0.95);
}
</style>
