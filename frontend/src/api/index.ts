import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add retry logic for network errors
api.interceptors.response.use(undefined, async (err) => {
  const config = err.config;
  
  // If config does not exist or the retry option is not set, reject
  if (!config || !config.retry) {
    return Promise.reject(err);
  }
  
  // Set the variable for keeping track of the retry count
  config.__retryCount = config.__retryCount || 0;
  
  // Check if we've maxed out the total number of retries
  if (config.__retryCount >= config.retry) {
    return Promise.reject(err);
  }
  
  // Increase the retry count
  config.__retryCount += 1;
  
  // Create new promise to handle exponential backoff
  const backoff = new Promise(function(resolve) {
    setTimeout(function() {
      resolve(null);
    }, config.retryDelay || 1000);
  });
  
  // Return the promise in which recalls axios to retry the request
  await backoff;
  return api(config);
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
