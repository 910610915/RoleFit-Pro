import api from './index'

export const dbApi = {
  exportSQLite: () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    window.open(`${baseUrl}/db/export/sqlite`, '_blank')
  },
  
  exportMySQL: () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    window.open(`${baseUrl}/db/export/mysql`, '_blank')
  },
  
  exportPostgreSQL: () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    window.open(`${baseUrl}/db/export/postgresql`, '_blank')
  },
  
  importDB: (file: File) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    const formData = new FormData()
    formData.append('file', file)
    
    return fetch(`${baseUrl}/db/import`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }).then(res => res.json())
  }
}
