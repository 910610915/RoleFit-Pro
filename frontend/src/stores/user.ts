/**
 * 用户权限 Store
 * 管理当前用户的角色和权限信息
 */

import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export interface UserPermissions {
  role: string
  role_name: string
  permissions: string[]
  level: number
  department?: string
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as {
      id: string
      username: string
      email: string
      full_name: string
      role: string
    } | null,
    permissions: null as UserPermissions | null,
    token: localStorage.getItem('token') || null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role || 'viewer',
    userLevel: (state) => state.permissions?.level || 0,
    userPermissions: (state) => state.permissions?.permissions || [],
    
    // 检查是否有特定权限
    hasPermission: (state) => (permission: string) => {
      if (!state.permissions) return false
      const perms = state.permissions.permissions
      // * 表示所有权限
      if (perms.includes('*')) return true
      return perms.includes(permission)
    },
    
    // 检查是否有特定角色
    hasRole: (state) => (roles: string | string[]) => {
      if (!state.user) return false
      const roleArray = Array.isArray(roles) ? roles : [roles]
      return roleArray.includes(state.user.role)
    },
    
    // 是否是管理员
    isAdmin: (state) => {
      if (!state.permissions) return false
      return state.permissions.permissions.includes('*') || 
             state.user?.role === 'super_admin' ||
             state.user?.role === 'it_admin'
    },
  },

  actions: {
    // 设置用户信息
    setUser(user: any) {
      this.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        localStorage.removeItem('user')
      }
    },

    // 设置 Token
    setToken(token: string | null) {
      this.token = token
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    },

    // 设置权限信息
    setPermissions(permissions: UserPermissions) {
      this.permissions = permissions
    },

    // 从本地存储恢复用户信息
    restoreUser() {
      const userStr = localStorage.getItem('user')
      const token = localStorage.getItem('token')
      if (userStr && token) {
        this.user = JSON.parse(userStr)
        this.token = token
        return true
      }
      return false
    },

    // 获取当前用户权限
    async fetchPermissions() {
      try {
        const response = await authApi.me()
        // 调用 /api/auth/me 获取用户信息和权限
        if (response.data) {
          this.setUser(response.data)
          
          // 获取角色权限
          try {
            const permResponse = await fetch('/api/roles/my-permissions', {
              headers: {
                'Authorization': `Bearer ${this.token}`
              }
            })
            if (permResponse.ok) {
              const permData = await permResponse.json()
              this.setPermissions(permData)
            }
          } catch (e) {
            console.warn('Failed to fetch permissions:', e)
          }
        }
      } catch (error) {
        console.error('Failed to fetch user info:', error)
      }
    },

    // 登录
    async login(username: string, password: string) {
      try {
        const response = await authApi.login({ username, password })
        const { access_token, user } = response.data
        
        this.setToken(access_token)
        this.setUser(user)
        
        // 获取权限信息
        await this.fetchPermissions()
        
        return { success: true }
      } catch (error: any) {
        return { success: false, error: error.message }
      }
    },

    // 登出
    logout() {
      this.user = null
      this.permissions = null
      this.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    // 初始化 - 从本地存储恢复
    init() {
      this.restoreUser()
    }
  }
})
