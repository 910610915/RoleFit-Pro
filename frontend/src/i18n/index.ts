import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    app: {
      title: 'Hardware Benchmark System',
      logout: 'Logout'
    },
    nav: {
      dashboard: 'Dashboard',
      devices: 'Devices',
      tasks: 'Tasks',
      results: 'Results',
      standards: 'Standards',
      settings: 'Settings'
    },
    dashboard: {
      title: 'Dashboard',
      totalDevices: 'Total Devices',
      online: 'Online',
      offline: 'Offline',
      totalTasks: 'Total Tasks',
      pending: 'Pending',
      running: 'Running',
      totalTests: 'Total Tests',
      passed: 'Passed',
      failed: 'Failed',
      averageScore: 'Average Score',
      deviceStatus: 'Device Status Distribution',
      scoreTrend: 'Score Trend (Last 30 Days)',
      devicesByDept: 'Devices by Department',
      department: 'Department',
      deviceCount: 'Total Devices',
      avgScore: 'Avg Score'
    },
    devices: {
      title: 'Device Management',
      addDevice: 'Add Device',
      deviceName: 'Device Name',
      ipAddress: 'IP Address',
      department: 'Department',
      position: 'Position',
      cpu: 'CPU',
      gpu: 'GPU',
      lastSeen: 'Last Seen',
      status: 'Status',
      actions: 'Actions',
      view: 'View',
      delete: 'Delete',
      confirmDelete: 'Are you sure you want to delete this device?'
    },
    tasks: {
      title: 'Task Management',
      createTask: 'Create Task',
      taskName: 'Task Name',
      taskType: 'Task Type',
      status: 'Status',
      createdAt: 'Created At',
      actions: 'Actions',
      view: 'View',
      execute: 'Execute',
      cancel: 'Cancel',
      pending: 'Pending',
      running: 'Running',
      completed: 'Completed',
      failed: 'Failed'
    },
    results: {
      title: 'Test Results',
      startTime: 'Start Time',
      status: 'Status',
      score: 'Score',
      actions: 'Actions',
      view: 'View',
      passed: 'Passed',
      failed: 'Failed',
      warning: 'Warning',
      partial: 'Partial'
    },
    standards: {
      title: 'Standard Management',
      positionName: 'Position Name',
      positionCode: 'Position Code',
      description: 'Description',
      cpuRequired: 'CPU Required',
      gpuRequired: 'GPU Required',
      ramRequired: 'RAM Required',
      actions: 'Actions'
    },
    settings: {
      title: 'Settings',
      apiUrl: 'API Base URL',
      refreshInterval: 'Refresh Interval (seconds)',
      notifyTaskComplete: 'Notify on Task Complete',
      notifyDeviceOffline: 'Notify on Device Offline',
      notifyStandardFail: 'Notify on Standard Fail',
      save: 'Save',
      saved: 'Settings saved!'
    },
    common: {
      search: 'Search',
      filter: 'Filter',
      refresh: 'Refresh',
      loading: 'Loading...',
      noData: 'No Data',
      confirm: 'Confirm',
      cancel: 'Cancel',
      success: 'Success',
      error: 'Error'
    }
  },
  'zh-CN': {
    app: {
      title: '硬件性能基准测试系统',
      logout: '退出登录'
    },
    nav: {
      dashboard: '仪表盘',
      devices: '设备管理',
      tasks: '任务管理',
      results: '测试结果',
      standards: '标准管理',
      settings: '系统设置'
    },
    dashboard: {
      title: '仪表盘',
      totalDevices: '设备总数',
      online: '在线',
      offline: '离线',
      totalTasks: '任务总数',
      pending: '待执行',
      running: '执行中',
      totalTests: '测试总数',
      passed: '通过',
      failed: '失败',
      averageScore: '平均分数',
      deviceStatus: '设备状态分布',
      scoreTrend: '分数趋势（近30天）',
      devicesByDept: '部门设备统计',
      department: '部门',
      deviceCount: '设备数量',
      avgScore: '平均分数'
    },
    devices: {
      title: '设备管理',
      addDevice: '添加设备',
      deviceName: '设备名称',
      ipAddress: 'IP地址',
      department: '部门',
      position: '岗位',
      cpu: '处理器',
      gpu: '显卡',
      lastSeen: '最后在线',
      status: '状态',
      actions: '操作',
      view: '查看',
      delete: '删除',
      confirmDelete: '确定要删除这个设备吗？'
    },
    tasks: {
      title: '任务管理',
      createTask: '创建任务',
      taskName: '任务名称',
      taskType: '任务类型',
      status: '状态',
      createdAt: '创建时间',
      actions: '操作',
      view: '查看',
      execute: '执行',
      cancel: '取消',
      pending: '待执行',
      running: '执行中',
      completed: '已完成',
      failed: '失败'
    },
    results: {
      title: '测试结果',
      startTime: '开始时间',
      status: '状态',
      score: '分数',
      actions: '操作',
      view: '查看',
      passed: '通过',
      failed: '失败',
      warning: '警告',
      partial: '部分通过'
    },
    standards: {
      title: '标准管理',
      positionName: '岗位名称',
      positionCode: '岗位编码',
      description: '描述',
      cpuRequired: 'CPU要求',
      gpuRequired: 'GPU要求',
      ramRequired: '内存要求',
      actions: '操作'
    },
    settings: {
      title: '系统设置',
      apiUrl: 'API地址',
      refreshInterval: '刷新间隔（秒）',
      notifyTaskComplete: '任务完成通知',
      notifyDeviceOffline: '设备离线通知',
      notifyStandardFail: '标准未达标通知',
      save: '保存',
      saved: '设置已保存！'
    },
    common: {
      search: '搜索',
      filter: '筛选',
      refresh: '刷新',
      loading: '加载中...',
      noData: '暂无数据',
      confirm: '确认',
      cancel: '取消',
      success: '成功',
      error: '错误'
    }
  }
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en',
  messages
})

export default i18n
