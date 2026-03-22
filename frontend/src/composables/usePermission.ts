/**
 * 权限检查 Composable
 * 提供在组件中检查权限的便捷方法
 */

import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

// 权限常量
export const PERMISSIONS = {
  DEVICES_READ: 'devices:read',
  DEVICES_WRITE: 'devices:write',
  DEVICES_DELETE: 'devices:delete',
  USERS_READ: 'users:read',
  USERS_WRITE: 'users:write',
  USERS_DELETE: 'users:delete',
  ALARMS_READ: 'alarms:read',
  ALARMS_WRITE: 'alarms:write',
  TASKS_READ: 'tasks:read',
  TASKS_WRITE: 'tasks:write',
  TASKS_DELETE: 'tasks:delete',
  PERFORMANCE_READ: 'performance:read',
  CONTROL_EXECUTE: 'control:execute',
  AUDIT_READ: 'audit:read',
  AUDIT_WRITE: 'audit:write',
  SETTINGS_READ: 'settings:read',
  SETTINGS_WRITE: 'settings:write',
  ROLES_READ: 'roles:read',
  ROLES_WRITE: 'roles:write',
}

// 角色常量
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  IT_ADMIN: 'it_admin',
  OPS: 'ops',
  DEPT_ADMIN: 'dept_admin',
  VIEWER: 'viewer',
}

// 路由权限映射
export const ROUTE_PERMISSIONS: Record<string, {
  roles?: string[]
  permissions?: string[]
}> = {
  '/system': {
    roles: ['super_admin', 'it_admin'],
    permissions: [PERMISSIONS.SETTINGS_READ, PERMISSIONS.ROLES_READ]
  },
  '/settings': {
    permissions: [PERMISSIONS.SETTINGS_READ]
  },
}

export function usePermission() {
  const userStore = useUserStore()

  // 检查是否有特定权限
  const hasPermission = (permission: string): boolean => {
    return userStore.hasPermission(permission)
  }

  // 检查是否有特定角色
  const hasRole = (roles: string | string[]): boolean => {
    return userStore.hasRole(roles)
  }

  // 检查是否是管理员
  const isAdmin = computed(() => userStore.isAdmin)

  // 检查是否可以访问路由
  const canAccessRoute = (routePath: string): boolean => {
    const routeConfig = ROUTE_PERMISSIONS[routePath]
    
    // 如果没有配置权限要求，允许访问
    if (!routeConfig) return true
    
    // 检查角色要求
    if (routeConfig.roles) {
      if (!userStore.hasRole(routeConfig.roles)) {
        return false
      }
    }
    
    // 检查权限要求
    if (routeConfig.permissions) {
      for (const perm of routeConfig.permissions) {
        if (!userStore.hasPermission(perm)) {
          return false
        }
      }
    }
    
    return true
  }

  // 创建 v-if 指令用的权限检查函数
  const createPermissionGuard = (permission: string) => {
    return computed(() => hasPermission(permission))
  }

  // 创建角色检查函数
  const createRoleGuard = (roles: string | string[]) => {
    return computed(() => hasRole(roles))
  }

  return {
    hasPermission,
    hasRole,
    isAdmin,
    canAccessRoute,
    createPermissionGuard,
    createRoleGuard,
    PERMISSIONS,
    ROLES,
  }
}
