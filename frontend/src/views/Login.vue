<template>
  <div class="landing-page">
    <!-- White Background with Floating Particles -->
    <ParticleBackgroundWhite />
    
    <!-- Top Right Login Button -->
    <div class="top-right">
      <n-button 
        class="login-btn"
        @click="showLogin = true"
      >
        登录
      </n-button>
    </div>
    
    <!-- Main Content -->
    <div class="content">
      <!-- Hero Section -->
      <section class="hero">
        <h1 class="hero-title">
          RoleFit Pro
        </h1>
        <p class="hero-subtitle">
          智能硬件性能基准测试与岗位匹配平台
        </p>
        <p class="hero-desc">
          专为游戏开发公司打造的硬件管理解决方案
        </p>
      </section>
      
      <!-- Features -->
      <section class="features">
        <div class="feature" v-for="(feature, index) in features" :key="index">
          <span class="feature-num">{{ feature.num }}</span>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.desc }}</p>
        </div>
      </section>
      
      <!-- Supported Software - Scroll Trigger Animation -->
      <section 
        class="software-section" 
        ref="softwareSectionRef"
      >
        <h2 class="section-title">支持的软件</h2>
        <p class="section-desc">针对游戏开发岗位的标准化性能测试</p>
        
        <div class="software-grid">
          <div 
            class="software-card" 
            v-for="(software, index) in softwareList" 
            :key="index"
            :class="{ 'is-visible': software.visible, 'is-animated': animationTriggered }"
            :style="{ 
              opacity: software.visible ? 1 : 0,
              transform: software.visible ? 'translateY(0) scale(1)' : 'translateY(60px) scale(0.8)',
              transitionDelay: `${index * 80}ms`
            }            "
          >
            <div class="software-icon">
              <img :src="software.iconUrl" :alt="software.name" />
            </div>
            <div class="software-info">
              <h4>{{ software.name }}</h4>
              <p>{{ software.category }}</p>
              <span class="software-positions">{{ software.positions }}</span>
            </div>
          </div>
        </div>
      </section>
      
      <!-- Stats -->
      <section class="stats">
        <div class="stat" v-for="(stat, index) in stats" :key="index">
          <span class="stat-num">{{ stat.num }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </section>

      <!-- Use Cases -->
      <section class="use-cases">
        <h2 class="section-title">适用岗位</h2>
        <p class="section-desc">覆盖游戏开发全流程的硬件性能评估</p>
        
        <div class="use-cases-grid">
          <div class="use-case-card" v-for="(uc, index) in useCases" :key="index">
            <n-icon size="48" class="use-case-icon">
              <component :is="uc.icon" />
            </n-icon>
            <h4>{{ uc.title }}</h4>
            <p>{{ uc.desc }}</p>
            <div class="use-case-software">
              <span v-for="sw in uc.software" :key="sw">{{ sw }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Workflow -->
      <section class="workflow">
        <h2 class="section-title">工作流程</h2>
        <p class="section-desc">全自动化硬件性能评估流程</p>
        
        <div class="workflow-steps">
          <div class="workflow-step" v-for="(step, index) in workflow" :key="index">
            <div class="step-num" :style="{ animationDelay: `${index * 0.2}s` }">{{ index + 1 }}</div>
            <div class="step-content">
              <h4>{{ step.title }}</h4>
              <p>{{ step.desc }}</p>
            </div>
            <div class="step-arrow" v-if="index < workflow.length - 1">→</div>
          </div>
        </div>
      </section>

      <!-- Screenshots -->
      <section class="screenshots" ref="screenshotsRef">
        <h2 class="section-title">系统界面</h2>
        <p class="section-desc">直观的硬件管理与性能分析平台</p>
        
        <div class="screenshots-grid">
          <div 
            class="screenshot-card" 
            v-for="(shot, index) in screenshots" 
            :key="index"
            :class="{ 'is-visible': screenshotVisible }"
            :style="{ 
              opacity: screenshotVisible ? 1 : 0,
              transform: screenshotVisible ? 'translateY(0)' : 'translateY(40px)',
              transitionDelay: `${index * 120}ms`
            }"
          >
            <div class="screenshot-placeholder">
              <n-icon size="48">
                <component :is="shot.icon" />
              </n-icon>
            </div>
            <h4>{{ shot.title }}</h4>
            <p>{{ shot.desc }}</p>
          </div>
        </div>
      </section>

      <!-- 3D Computers -->
    </div>
    
    <!-- Login Modal -->
    <n-modal v-model:show="showLogin" preset="card" :style="{ width: '420px' }" :bordered="false" :closable="true" class="login-modal" :mask-closable="true">
      <div class="modal-content">
        <!-- Logo Area -->
        <div class="modal-logo">
          <div class="logo-icon">
            <n-icon size="36">
              <Desktop />
            </n-icon>
          </div>
          <h2 class="modal-title">RoleFit Pro</h2>
          <p class="modal-desc">智能硬件性能基准测试平台</p>
        </div>
        
        <!-- Login Form -->
        <div class="form-area">
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <PersonCircle />
            </n-icon>
            <n-input 
              v-model:value="formData.username" 
              placeholder="请输入用户名"
              size="large"
              class="login-input"
            />
          </div>
          
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <Key />
            </n-icon>
            <n-input 
              v-model:value="formData.password" 
              type="password"
              placeholder="请输入密码"
              size="large"
              class="login-input"
              @keyup.enter="handleLogin"
            />
          </div>
        </div>
        
        <!-- Login Button -->
        <n-button 
          type="primary" 
          block 
          size="large"
          :loading="loading" 
          @click="handleLogin"
          class="modal-btn"
        >
          {{ loading ? '登录中...' : '立即登录' }}
        </n-button>
        
        <!-- Register Link -->
        <div class="register-link">
          还没有账号？ <a @click="openRegister">立即注册</a>
        </div>
        
        <!-- Hint -->
        <p class="modal-hint">默认账户: admin / admin123</p>
      </div>
    </n-modal>
    
    <!-- Register Modal -->
    <n-modal v-model:show="showRegister" preset="card" :style="{ width: '420px' }" :bordered="false" :closable="true" class="login-modal" :mask-closable="true">
      <div class="modal-content">
        <!-- Logo Area -->
        <div class="modal-logo">
          <div class="logo-icon">
            <n-icon size="36">
              <Desktop />
            </n-icon>
          </div>
          <h2 class="modal-title">注册账号</h2>
          <p class="modal-desc">创建您的RoleFit Pro账号</p>
        </div>
        
        <!-- Register Form -->
        <div class="form-area">
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <PersonCircle />
            </n-icon>
            <n-input 
              v-model:value="registerData.username" 
              placeholder="请输入用户名"
              size="large"
              class="login-input"
            />
          </div>
          
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <Key />
            </n-icon>
            <n-input 
              v-model:value="registerData.password" 
              type="password"
              placeholder="请输入密码"
              size="large"
              class="login-input"
            />
          </div>
          
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <Key />
            </n-icon>
            <n-input 
              v-model:value="registerData.confirmPassword" 
              type="password"
              placeholder="请确认密码"
              size="large"
              class="login-input"
              @keyup.enter="handleRegister"
            />
          </div>
          
          <div class="input-group">
            <n-icon class="input-icon" size="20">
              <Mail />
            </n-icon>
            <n-input 
              v-model:value="registerData.email" 
              placeholder="请输入邮箱（可选）"
              size="large"
              class="login-input"
            />
          </div>
        </div>
        
        <!-- Register Button -->
        <n-button 
          type="primary" 
          block 
          size="large"
          :loading="registerLoading" 
          @click="handleRegister"
          class="modal-btn"
        >
          {{ registerLoading ? '注册中...' : '立即注册' }}
        </n-button>
        
        <!-- Login Link -->
        <div class="register-link">
          已有账号？ <a @click="openLogin">立即登录</a>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NModal, NForm, NFormItem, NInput, NIcon, useMessage } from 'naive-ui'
import { login, register } from '@/api/auth'
import ParticleBackgroundWhite from '@/components/ParticleBackgroundWhite.vue'
import {
  CodeSlash,
  ColorPalette,
  Sparkles,
  Videocam,
  Desktop,
  BarChart,
  PersonCircle,
  List,
  Key,
  Mail
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

// Icon render function
const renderIcon = (icon: any) => () => h(NIcon, null, { default: () => h(icon) })

const softwareSectionRef = ref()
const showLogin = ref(false)
const showRegister = ref(false)
const formRef = ref()
const loading = ref(false)
const registerLoading = ref(false)
const animationTriggered = ref(false)
const formData = ref({
  username: '',
  password: ''
})

// Registration data
const registerData = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// Features data
const features = [
  { num: '01', title: '性能基准测试', desc: '针对不同岗位运行标准化性能测试' },
  { num: '02', title: '智能岗位匹配', desc: '分析设备与岗位需求的匹配程度' },
  { num: '03', title: '数据驱动决策', desc: '识别性能瓶颈，提供升级建议' },
]

// Software list
const softwareList = ref([
  { name: 'Visual Studio', category: '开发工具', positions: '程序开发', iconText: 'VS', iconUrl: '/software-logos/Visual Studio.png', visible: false },
  { name: 'Unreal Engine', category: '游戏引擎', positions: '程序/TA', iconText: 'UE', iconUrl: '/software-logos/Unreal Engine.png', visible: false },
  { name: 'Unity', category: '游戏引擎', positions: '程序开发', iconText: 'Unity', iconUrl: '/software-logos/Unity.png', visible: false },
  { name: 'Blender', category: '3D建模', positions: '美术/动画', iconText: 'BL', iconUrl: '/software-logos/Blender.png', visible: false },
  { name: 'Maya', category: '3D建模', positions: '美术/动画', iconText: 'MAYA', iconUrl: '/software-logos/3Dmax.png', visible: false },
  { name: 'Photoshop', category: '图像处理', positions: '美术/UI', iconText: 'PS', iconUrl: '/software-logos/Photoshop.png', visible: false },
  { name: 'After Effects', category: '特效合成', positions: 'VFX/视频', iconText: 'AE', iconUrl: '/software-logos/After Effects.png', visible: false },
  { name: 'Premiere Pro', category: '视频编辑', positions: '视频制作', iconText: 'PR', iconUrl: '/software-logos/Premiere Pro.png', visible: false },
])

const stats = [
  { num: '40+', label: '测试脚本' },
  { num: '10+', label: '软件支持' },
  { num: '100%', label: '自动化' },
]

// Use Cases data
const useCases = [
  { icon: CodeSlash, title: '程序开发', desc: '编译、调试、构建性能评估', software: ['VS', 'UE', 'Unity', 'VSCode'] },
  { icon: ColorPalette, title: '美术设计', desc: '建模、渲染、贴图制作', software: ['Blender', 'Maya', 'PS', 'ZBrush'] },
  { icon: Sparkles, title: '技术美术', desc: 'Shader、效果、性能优化', software: ['UE', 'Unity', 'Houdini', 'Substance'] },
  { icon: Videocam, title: '视频制作', desc: '剪辑、特效、合成', software: ['PR', 'AE', 'DaVinci', 'C4D'] },
]

// Workflow data
const workflow = [
  { title: '设备接入', desc: 'Agent 自动注册到平台' },
  { title: '硬件检测', desc: '自动采集 CPU/GPU/内存信息' },
  { title: '性能测试', desc: '运行岗位标准化测试脚本' },
  { title: '匹配分析', desc: '对比岗位需求与硬件性能' },
  { title: '报告生成', desc: '输出详细的性能评估报告' },
]

// Screenshots data
const screenshotsRef = ref()
const screenshotVisible = ref(false)
const screenshots = [
  { icon: Desktop, title: '设备管理', desc: '集中查看所有开发设备状态' },
  { icon: BarChart, title: '性能分析', desc: '详细的硬件性能指标展示' },
  { icon: PersonCircle, title: '岗位匹配', desc: '智能匹配设备与岗位需求' },
  { icon: List, title: '任务管理', desc: '创建和调度性能测试任务' },
]



const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' }
}

const handleLogin = async () => {
  try {
    if (!formData.value.username || !formData.value.password) {
      message.error('请输入用户名和密码')
      return
    }
    
    loading.value = true
    
    const res = await login(formData.value)
    const data = res.data
    
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    
    message.success('登录成功')
    showLogin.value = false
    router.push('/')
  } catch (e: any) {
    console.error('Login error:', e)
    const errorMsg = e.response?.data?.detail || e.message || '登录失败，请检查用户名和密码'
    message.error(errorMsg)
  } finally {
    loading.value = false
  }
}

// Open register modal
const openRegister = () => {
  showLogin.value = false
  showRegister.value = true
}

// Open login modal
const openLogin = () => {
  showRegister.value = false
  showLogin.value = true
}

// Handle registration
const handleRegister = async () => {
  try {
    if (!registerData.value.username || !registerData.value.password) {
      message.error('请输入用户名和密码')
      return
    }
    
    if (registerData.value.password !== registerData.value.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }
    
    if (registerData.value.password.length < 6) {
      message.error('密码长度不能少于6位')
      return
    }
    
    registerLoading.value = true
    
    const res = await register({
      username: registerData.value.username,
      password: registerData.value.password,
      email: registerData.value.email || undefined
    })
    
    message.success('注册成功，请登录')
    showRegister.value = false
    showLogin.value = true
    
    // Clear form
    registerData.value = {
      username: '',
      password: '',
      confirmPassword: '',
      email: ''
    }
  } catch (e: any) {
    console.error('Register error:', e)
    const errorMsg = e.response?.data?.detail || e.message || '注册失败，请稍后重试'
    message.error(errorMsg)
  } finally {
    registerLoading.value = false
  }
}

// Trigger animation when section comes into view
const triggerSoftwareAnimation = () => {
  if (animationTriggered.value) return
  
  animationTriggered.value = true
  softwareList.value.forEach((software, index) => {
    setTimeout(() => {
      software.visible = true
    }, index * 80)
  })
}

// Use Intersection Observer to trigger animation when section is visible
onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          triggerSoftwareAnimation()
        }
      })
    },
    { threshold: 0.3 }
  )
  
  const screenshotObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          screenshotVisible.value = true
        }
      })
    },
    { threshold: 0.2 }
  )
  
  if (softwareSectionRef.value) {
    observer.observe(softwareSectionRef.value)
  }
  
  if (screenshotsRef.value) {
    screenshotObserver.observe(screenshotsRef.value)
  }
})
</script>

<style scoped lang="scss">
.landing-page {
  position: relative;
  min-height: 200vh;
  background: #fff;
  color: #000;
}

.top-right {
  position: fixed;
  top: 20px;
  right: 24px;
  z-index: 100;
  
  .login-btn {
    background: #000;
    color: #fff;
    border: none;
    padding: 12px 28px;
    border-radius: 28px;
    font-size: 15px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: #333;
      transform: scale(1.05);
    }
  }
}

.content {
  position: relative;
  z-index: 10;
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px;
}

.hero {
  text-align: center;
  padding: 40px 0 60px;
  min-height: auto;
  
  .hero-title {
    font-size: 96px;
    font-weight: 800;
    letter-spacing: -3px;
    margin: 0 0 20px 0;
    color: #000;
  }
  
  .hero-subtitle {
    font-size: 32px;
    font-weight: 400;
    color: #333;
    margin: 0 0 8px 0;
  }
  
  .hero-desc {
    font-size: 16px;
    color: #666;
    margin: 0;
  }
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 48px;
  padding: 60px 0;
  
  .feature {
    text-align: left;
    
    .feature-num {
      display: block;
      font-size: 20px;
      color: #999;
      margin-bottom: 16px;
      font-family: monospace;
    }
    
    h3 {
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: #000;
    }
    
    p {
      font-size: 18px;
      color: #666;
      margin: 0;
      line-height: 1.6;
    }
  }
}

.software-section {
  padding: 80px 0;
  cursor: default;
  
  .section-title {
    font-size: 48px;
    font-weight: 600;
    text-align: center;
    margin: 0 0 12px 0;
    color: #000;
  }
  
  .section-desc {
    font-size: 20px;
    color: #666;
    text-align: center;
    margin: 0 0 40px 0;
  }
}

.software-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  
  .software-card {
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 16px;
    padding: 28px 20px;
    text-align: center;
    cursor: pointer;
    transition: opacity 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    opacity: 0;
    transform: translateY(60px) scale(0.8);
    
    &.is-visible {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
    
    &:hover {
      background: #fff;
      border-color: #ddd;
      box-shadow: 0 12px 40px rgba(0,0,0,0.12);
      transform: translateY(-8px) scale(1.02) !important;
      transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.2s ease-out !important;
      transition-delay: 0ms !important;
    }
    
    .software-icon {
      width: 80px;
      height: 80px;
      background: transparent;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      
      img {
        width: 64px;
        height: 64px;
        object-fit: contain;
      }
    }
    
    .software-info {
      h4 {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 6px 0;
        color: #000;
      }
      
      p {
        font-size: 13px;
        color: #666;
        margin: 0 0 10px 0;
      }
      
      .software-positions {
        font-size: 11px;
        color: #999;
        background: #f0f0f0;
        padding: 3px 10px;
        border-radius: 5px;
      }
    }
  }
}

.stats {
  display: flex;
  justify-content: center;
  gap: 80px;
  padding: 60px 0;
  
  .stat {
    text-align: center;
    
    .stat-num {
      display: block;
      font-size: 48px;
      font-weight: 700;
      color: #000;
    }
    
    .stat-label {
      font-size: 14px;
      color: #999;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
  }
}

:deep(.login-modal) {
  .n-card {
    background: #fff;
    border-radius: 20px;
    border: 1px solid #eee;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  }
}

.modal-content {
  padding: 8px;
  
  .modal-logo {
    text-align: center;
    margin-bottom: 32px;
    
    .logo-icon {
      width: 72px;
      height: 72px;
      background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
      border-radius: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      color: #fff;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    
    .modal-title {
      font-size: 26px;
      font-weight: 700;
      margin: 0 0 8px 0;
      color: #000;
      letter-spacing: 1px;
    }
    
    .modal-desc {
      font-size: 14px;
      color: #888;
      margin: 0;
    }
  }
  
  .form-area {
    margin-bottom: 24px;
    
    .input-group {
      position: relative;
      margin-bottom: 16px;
      
      .input-icon {
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        color: #999;
        z-index: 1;
      }
      
      .login-input {
        padding-left: 48px;
        
        :deep(.n-input__input-el) {
          font-size: 15px;
        }
      }
    }
  }
  
  .modal-btn {
    background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
    border: none;
    border-radius: 12px;
    height: 52px;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 2px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    
    &:hover {
      background: linear-gradient(135deg, #333 0%, #555 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    }
  }
  
  .modal-hint {
    text-align: center;
    font-size: 13px;
    color: #999;
    margin: 20px 0 0 0;
    padding-top: 16px;
    border-top: 1px solid #eee;
  }
  
  .register-link {
    text-align: center;
    font-size: 14px;
    color: #666;
    margin: 16px 0 0 0;
    
    a {
      color: #000;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

// Use Cases Section
.use-cases {
  padding: 100px 0;
  
  .use-cases-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 32px;
  }
  
  .use-case-card {
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 20px;
    padding: 36px 28px;
    text-align: center;
    transition: all 0.3s ease;
    
    &:hover {
      background: #fff;
      border-color: #ddd;
      box-shadow: 0 16px 48px rgba(0,0,0,0.1);
      transform: translateY(-8px);
    }
    
    .use-case-icon {
      font-size: 48px;
      margin-bottom: 20px;
    }
    
    h4 {
      font-size: 22px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: #000;
    }
    
    p {
      font-size: 15px;
      color: #666;
      margin: 0 0 20px 0;
      line-height: 1.5;
    }
    
    .use-case-software {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;
      
      span {
        font-size: 12px;
        color: #333;
        background: #eee;
        padding: 4px 12px;
        border-radius: 6px;
      }
    }
  }
}

// Workflow Section
.workflow {
  padding: 100px 0;
  
  .workflow-steps {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 20px;
    margin-top: 20px;
  }
  
  .workflow-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
    flex: 1;
    max-width: 200px;
    
    .step-num {
      width: 56px;
      height: 56px;
      background: #000;
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 20px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-10px);
      }
    }
    
    .step-content {
      h4 {
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: #000;
      }
      
      p {
        font-size: 14px;
        color: #666;
        margin: 0;
        line-height: 1.5;
      }
    }
    
    .step-arrow {
      position: absolute;
      right: -30px;
      top: 20px;
      font-size: 28px;
      color: #ccc;
    }
  }
}

// Screenshots Section
.screenshots {
  padding: 100px 0;
  
  .screenshots-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 28px;
  }
  
  .screenshot-card {
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    transition: opacity 0.4s ease, transform 0.4s ease;
    opacity: 0;
    transform: translateY(40px);
    
    &.is-visible {
      opacity: 1;
      transform: translateY(0);
    }
    
    &:hover {
      background: #fff;
      border-color: #ddd;
      box-shadow: 0 16px 48px rgba(0,0,0,0.1);
      transform: translateY(-8px) !important;
      transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.2s ease-out !important;
      transition-delay: 0ms !important;
    }
    
    .screenshot-placeholder {
      width: 100%;
      height: 140px;
      background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 20px;
      
      span {
        font-size: 56px;
      }
    }
    
    h4 {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: #000;
    }
    
    p {
      font-size: 14px;
      color: #666;
      margin: 0;
    }
  }
}

@media (max-width: 768px) {
  .hero .hero-title {
    font-size: 48px;
  }
  
  .features {
    grid-template-columns: 1fr;
    gap: 32px;
  }
  
  .software-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats {
    gap: 40px;
    
    .stat-num {
      font-size: 36px;
    }
  }
}
</style>
