<template>
  <div class="test-software">
    <n-h1>支持的测试软件</n-h1>
    
    <n-alert type="info" style="margin-bottom: 24px">
      以下是系统支持的硬件性能测试软件。在目标设备上安装相应的测试软件后，可以执行真实的性能测试。
    </n-alert>

    <!-- CPU Tests -->
    <n-card title="CPU 测试软件" class="software-category">
      <n-space vertical>
        <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" item-responsive>
          <n-gi v-for="software in cpuSoftware" :key="software.name" span="3 m:1">
            <div class="software-item">
              <div class="software-icon-wrapper" :style="{ backgroundColor: software.iconColor }">
                <img :src="software.iconUrl" :alt="software.name" class="software-icon" />
              </div>
              <div class="software-info">
                <n-h3 class="software-name">{{ software.name }}</n-h3>
                <n-text depth="3" class="software-desc">{{ software.description }}</n-text>
                <n-space size="small" style="margin-top: 8px">
                  <n-tag v-for="feature in software.features" :key="feature" size="small" type="success">
                    {{ feature }}
                  </n-tag>
                </n-space>
                <n-button size="small" type="primary" style="margin-top: 12px" @click="openUrl(software.website)">
                  访问官网
                </n-button>
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-space>
    </n-card>

    <!-- GPU Tests -->
    <n-card title="GPU 测试软件" class="software-category">
      <n-space vertical>
        <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" item-responsive>
          <n-gi v-for="software in gpuSoftware" :key="software.name" span="3 m:1">
            <div class="software-item">
              <div class="software-icon-wrapper" :style="{ backgroundColor: software.iconColor }">
                <img :src="software.iconUrl" :alt="software.name" class="software-icon" />
              </div>
              <div class="software-info">
                <n-h3 class="software-name">{{ software.name }}</n-h3>
                <n-text depth="3" class="software-desc">{{ software.description }}</n-text>
                <n-space size="small" style="margin-top: 8px">
                  <n-tag v-for="feature in software.features" :key="feature" size="small" type="success">
                    {{ feature }}
                  </n-tag>
                </n-space>
                <n-button size="small" type="primary" style="margin-top: 12px" @click="openUrl(software.website)">
                  访问官网
                </n-button>
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-space>
    </n-card>

    <!-- Memory Tests -->
    <n-card title="内存 测试软件" class="software-category">
      <n-space vertical>
        <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" item-responsive>
          <n-gi v-for="software in memorySoftware" :key="software.name" span="3 m:1">
            <div class="software-item">
              <div class="software-icon-wrapper" :style="{ backgroundColor: software.iconColor }">
                <img :src="software.iconUrl" :alt="software.name" class="software-icon" />
              </div>
              <div class="software-info">
                <n-h3 class="software-name">{{ software.name }}</n-h3>
                <n-text depth="3" class="software-desc">{{ software.description }}</n-text>
                <n-space size="small" style="margin-top: 8px">
                  <n-tag v-for="feature in software.features" :key="feature" size="small" type="success">
                    {{ feature }}
                  </n-tag>
                </n-space>
                <n-button size="small" type="primary" style="margin-top: 12px" @click="openUrl(software.website)">
                  访问官网
                </n-button>
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-space>
    </n-card>

    <!-- Disk Tests -->
    <n-card title="磁盘 测试软件" class="software-category">
      <n-space vertical>
        <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" item-responsive>
          <n-gi v-for="software in diskSoftware" :key="software.name" span="3 m:1">
            <div class="software-item">
              <div class="software-icon-wrapper" :style="{ backgroundColor: software.iconColor }">
                <img :src="software.iconUrl" :alt="software.name" class="software-icon" />
              </div>
              <div class="software-info">
                <n-h3 class="software-name">{{ software.name }}</n-h3>
                <n-text depth="3" class="software-desc">{{ software.description }}</n-text>
                <n-space size="small" style="margin-top: 8px">
                  <n-tag v-for="feature in software.features" :key="feature" size="small" type="success">
                    {{ feature }}
                  </n-tag>
                </n-space>
                <n-button size="small" type="primary" style="margin-top: 12px" @click="openUrl(software.website)">
                  访问官网
                </n-button>
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-space>
    </n-card>

    <!-- Comprehensive Tests -->
    <n-card title="综合测试软件" class="software-category">
      <n-space vertical>
        <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" item-responsive>
          <n-gi v-for="software in comprehensiveSoftware" :key="software.name" span="3 m:1">
            <div class="software-item">
              <div class="software-icon-wrapper" :style="{ backgroundColor: software.iconColor }">
                <img :src="software.iconUrl" :alt="software.name" class="software-icon" />
              </div>
              <div class="software-info">
                <n-h3 class="software-name">{{ software.name }}</n-h3>
                <n-text depth="3" class="software-desc">{{ software.description }}</n-text>
                <n-space size="small" style="margin-top: 8px">
                  <n-tag v-for="feature in software.features" :key="feature" size="small" type="success">
                    {{ feature }}
                  </n-tag>
                </n-space>
                <n-button size="small" type="primary" style="margin-top: 12px" @click="openUrl(software.website)">
                  访问官网
                </n-button>
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NH1, NAlert, NCard, NGrid, NGi, NSpace, NText, NH3, NTag, NButton } from 'naive-ui'

const openUrl = (url: string) => {
  window.open(url, '_blank')
}

// 使用本地图标文件夹
const getIconUrl = (filename: string) => {
  return `/software-logos/${filename}`
}

// CPU Software - 使用本地品牌图标
const cpuSoftware = [
  {
    name: 'Geekbench',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#FF6B00',
    description: '跨平台的处理器性能测试工具，支持Windows、Mac、Linux、iOS和Android。',
    features: ['CPU单核', 'CPU多核', 'GPU测试', 'AI测试'],
    website: 'https://www.geekbench.com/'
  },
  {
    name: 'Cinebench',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#000000',
    description: '基于Cinema 4D的CPU和GPU渲染性能测试软件，广泛用于评估处理器性能。',
    features: ['CPU单核', 'CPU多核', 'GPU渲染', 'OpenGL'],
    website: 'https://www.maxon.net/cinebench'
  },
  {
    name: 'Prime95',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#008000',
    description: '著名的CPU压力测试工具，用于测试CPU的稳定性和计算能力。',
    features: ['CPU压力测试', '稳定性测试', 'FFT测试', 'Torture Test'],
    website: 'https://www.mersenne.org/download/'
  },
  {
    name: 'AIDA64',
    iconUrl: getIconUrl('AIDA64.png'),
    iconColor: '#00A4E4',
    description: '系统信息、诊断和基准测试工具，提供全面的硬件检测和性能测试功能。',
    features: ['CPU测试', '内存测试', '缓存测试', '磁盘测试'],
    website: 'https://www.aida64.com/'
  },
  {
    name: 'PassMark',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#00B460',
    description: '全面的电脑性能基准测试软件，提供CPU、显卡、内存、磁盘等多项测试。',
    features: ['CPU测试', '2D图形', '3D图形', '内存', '磁盘'],
    website: 'https://www.passmark.com/products/performancetest.htm'
  }
]

// GPU Software
const gpuSoftware = [
  {
    name: '3DMark',
    iconUrl: getIconUrl('3DMark.png'),
    iconColor: '#FF6600',
    description: '业界最权威的图形性能基准测试软件，用于测试显卡的DirectX和OpenGL性能。',
    features: ['Time Spy', 'Port Royal', 'Fire Strike', '光追测试'],
    website: 'https://www.3dmark.com/'
  },
  {
    name: 'FurMark',
    iconUrl: getIconUrl('FurMark.png'),
    iconColor: '#5586A4',
    description: 'OpenGL基准测试工具，专门用于测试显卡的渲染性能和温度表现。',
    features: ['GPU压力测试', 'FPS测试', '温度监控', 'OGL4.0'],
    website: 'https://www.geeks3d.com/furmark/'
  },
  {
    name: 'Unigine',
    iconUrl: getIconUrl('Unigine.png'),
    iconColor: '#FF6600',
    description: '基于Unigine引擎的3D基准测试工具，支持DirectX 11/12和OpenGL。',
    features: ['8K渲染', 'VR测试', 'FPS基准', '极端压力'],
    website: 'https://unigine.com/products/superposition/'
  },
  {
    name: 'VRMark',
    iconUrl: getIconUrl('3DMark.png'),
    iconColor: '#00D4FF',
    description: '专业的VR性能基准测试工具，帮助评估设备的VR运行能力。',
    features: ['VR性能测试', 'Orange Room', 'Blue Room', 'Cyan Room'],
    website: 'https://www.3dmark.com/vrmark/'
  }
]

// Memory Software
const memorySoftware = [
  {
    name: 'MemTest86',
    iconUrl: getIconUrl('MemTest86.png'),
    iconColor: '#0099FF',
    description: '最权威的内存测试软件，在DOS环境下运行，不受操作系统影响。',
    features: ['内存错误检测', '启动盘测试', '多通道测试', 'ECC检测'],
    website: 'https://www.memtest86.com/'
  },
  {
    name: 'TestMem5',
    iconUrl: getIconUrl('TestMem5.png'),
    iconColor: '#333333',
    description: '专为内存超频设计的稳定性测试工具，是内存玩家必备的测试软件。',
    features: ['内存压力测试', '多种测试模式', '自定义配置', '快速测试'],
    website: 'https://github.com/1usmus/testmem5'
  },
  {
    name: 'AIDA64',
    iconUrl: getIconUrl('AIDA64.png'),
    iconColor: '#00A4E4',
    description: '提供全面的内存带宽和延迟测试，包括读取、写入、复制等多项测试。',
    features: ['内存读取', '内存写入', '内存复制', '延迟测试'],
    website: 'https://www.aida64.com/'
  }
]

// Disk Software
const diskSoftware = [
  {
    name: 'CrystalDiskMark',
    iconUrl: getIconUrl('CrystalDiskMark.png'),
    iconColor: '#0078D4',
    description: '简单易用的磁盘基准测试工具，测试硬盘的顺序和随机读写速度。',
    features: ['顺序读写', '4K随机', '队列深度', '多线程'],
    website: 'https://crystalmark.info/en/software/crystaldiskmark/'
  },
  {
    name: 'AS SSD',
    iconUrl: getIconUrl('AS SSD.png'),
    iconColor: '#0099FF',
    description: '专门用于测试固态硬盘性能的工具，评估SSD的真实性能表现。',
    features: ['AS SSD评分', '压缩测试', '4K对齐检测', '拷贝测试'],
    website: 'https://www.alex-is.de/PRODUKTE/Software/als_Werkzeuge/AS_SSD_Benchmark'
  },
  {
    name: 'ATTO',
    iconUrl: getIconUrl('ATTO.png'),
    iconColor: '#00A4E4',
    description: '业界标准的磁盘基准测试工具，测试不同数据块大小的传输速率。',
    features: ['块大小测试', '线性测试', 'IOPS测试', '延迟测试'],
    website: 'https://www.atto.com/disk-benchmark/'
  },
  {
    name: 'CrystalDiskInfo',
    iconUrl: getIconUrl('CrystalDiskInfo.png'),
    iconColor: '#0078D4',
    description: '磁盘健康状态监控工具，实时显示硬盘的SMART信息和温度。',
    features: ['健康监测', '温度监控', 'SMART信息', '告警功能'],
    website: 'https://crystalmark.info/en/software/crystaldiskinfo/'
  }
]

// Comprehensive Software
const comprehensiveSoftware = [
  {
    name: 'PCMark 10',
    iconUrl: getIconUrl('PCMark 10.png'),
    iconColor: '#FF6600',
    description: '全面的PC性能基准测试，模拟真实工作场景测试整机性能。',
    features: ['日常办公', '数字内容创作', '游戏性能', '电池续航'],
    website: 'https://www.3dmark.com/pcmark10/'
  },
  {
    name: 'UserBenchmark',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#FF6600',
    description: '用户驱动的硬件性能对比平台，帮助用户了解硬件在同类产品中的排名。',
    features: ['CPU对比', 'GPU对比', 'SSD对比', '用户评分'],
    website: 'https://userbenchmark.com/'
  },
  {
    name: 'Novabench',
    iconUrl: getIconUrl('Geekbench.png'),
    iconColor: '#0099FF',
    description: '快速的系统基准测试工具，简单操作即可获得完整的性能评分。',
    features: ['CPU测试', 'GPU测试', 'RAM测试', '磁盘测试'],
    website: 'https://novabench.com/'
  }
]
</script>

<style scoped>
.test-software {
  padding: 20px;
  max-width: 1600px;
}

.software-category {
  margin-bottom: 24px;
}

.software-item {
  display: flex;
  flex-direction: row;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  height: 100%;
}

.software-icon-wrapper {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  padding: 12px;
  background-color: #f5f5f5;
}

.software-icon {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.software-info {
  flex: 1;
  min-width: 0;
}

.software-name {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.software-desc {
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
