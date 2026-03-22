import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'DeviceList',
    component: () => import('@/views/Devices/DeviceList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devices/:id',
    name: 'DeviceDetail',
    component: () => import('@/views/Devices/DeviceDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'TaskList',
    component: () => import('@/views/Tasks/TaskList.vue'),
    meta: { requiresAuth: true, permission: 'tasks:read' }
  },
  {
    path: '/tasks/create',
    name: 'TaskCreate',
    component: () => import('@/views/Tasks/TaskCreate.vue'),
    meta: { requiresAuth: true, permission: 'tasks:write' }
  },
  {
    path: '/results',
    name: 'ResultList',
    component: () => import('@/views/Results/ResultList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/results/:id',
    name: 'ResultDetail',
    component: () => import('@/views/Results/ResultDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/compare',
    name: 'DeviceCompare',
    component: () => import('@/views/Compare/DeviceCompare.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/standards',
    name: 'StandardManage',
    component: () => import('@/views/Standards/StandardManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test-software',
    name: 'TestSoftware',
    component: () => import('@/views/TestSoftware.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/performance',
    name: 'Performance',
    component: () => import('@/views/Performance/Performance.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-chat',
    name: 'AIChat',
    component: () => import('@/views/AIChat/AIChat.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/positions',
    name: 'PositionList',
    component: () => import('@/views/Positions/PositionList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/software',
    name: 'SoftwareList',
    component: () => import('@/views/Software/SoftwareList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/scripts',
    name: 'ScriptList',
    component: () => import('@/views/Scripts/ScriptList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/executions',
    name: 'ExecutionList',
    component: () => import('@/views/Executions/ExecutionList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system',
    name: 'system',
    component: () => import('@/views/SystemManagement.vue'),
    meta: { requiresAuth: true, roles: ['super_admin', 'it_admin'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Auth and permission guard
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')
  
  // 初始化用户信息
  if (token && !userStore.user) {
    userStore.restoreUser()
    // 尝试获取完整用户信息和权限
    try {
      await userStore.fetchPermissions()
    } catch (e) {
      console.warn('Failed to fetch user permissions:', e)
    }
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
    return
  }
  
  // 如果已登录访问登录页，跳转到首页
  if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
    return
  }
  
  // 检查角色要求
  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles && requiredRoles.length > 0) {
    if (!userStore.hasRole(requiredRoles)) {
      // 没有权限，显示提示并跳转到首页
      console.warn(`Access denied to ${to.path}. Required roles: ${requiredRoles.join(', ')}`)
      next({ name: 'Dashboard' })
      return
    }
  }
  
  // 检查权限要求
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission && !userStore.hasPermission(requiredPermission)) {
    console.warn(`Access denied to ${to.path}. Required permission: ${requiredPermission}`)
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})

export default router
