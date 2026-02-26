import api from './index'

export interface FeatureCard {
  id: string
  card_key: string
  title: string
  description?: string
  icon?: string
  route?: string
  is_visible: boolean
  sort_order: number
  is_custom: boolean
}

export const featureCardApi = {
  list: () => api.get<{ items: FeatureCard[]; total: number }>('/feature-cards'),
  
  get: (id: string) => api.get<FeatureCard>(`/feature-cards/${id}`),
  
  create: (data: Partial<FeatureCard>) => api.post<FeatureCard>('/feature-cards', data),
  
  update: (id: string, data: Partial<FeatureCard>) => 
    api.put<FeatureCard>(`/feature-cards/${id}`, data),
  
  delete: (id: string) => api.delete(`/feature-cards/${id}`),
  
  reorder: (cardIds: string[]) => api.put<{ items: FeatureCard[]; total: number }>('/feature-cards/reorder', cardIds),
}
