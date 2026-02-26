import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

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
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks/create',
    name: 'TaskCreate',
    component: () => import('@/views/Tasks/TaskCreate.vue'),
    meta: { requiresAuth: true }
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Auth guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
