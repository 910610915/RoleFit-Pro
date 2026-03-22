import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './assets/styles/main.scss'
import { useUserStore } from './stores/user'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(naive)
app.use(i18n)

// 初始化用户状态
const userStore = useUserStore()
userStore.init()

app.mount('#app')
