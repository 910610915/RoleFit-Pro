import api from './index'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    email: string
    full_name: string
    role: string
  }
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  full_name?: string
}

export const authApi = {
  login: (data: LoginRequest) => 
    api.post<LoginResponse>('/auth/auth/login', data),
  
  register: (data: RegisterRequest) =>
    api.post<LoginResponse>('/auth/auth/register', data),

  me: () => 
    api.get('/auth/auth/me'),
  
  logout: () => 
    api.post('/auth/auth/logout')
}

// 导出login作为独立函数
export const login = authApi.login
export const register = authApi.register
