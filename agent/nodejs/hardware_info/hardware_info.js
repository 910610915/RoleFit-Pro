#!/usr/bin/env node
/**
 * Hardware Info - Using systeminformation library
 * Provides accurate hardware information for Windows
 */

const si = require('systeminformation');
const os = require('os');

/**
 * Get all hardware information
 */
async function getHardwareInfo() {
  try {
    // Get all data in parallel for speed
    const [
      cpu,
      cpuCurrentSpeed,
      memory,
      memLayout,
      diskLayout,
      graphics,
      osInfo,
      networkInterfaces
    ] = await Promise.all([
      si.cpu(),
      si.cpuCurrentSpeed(),
      si.mem(),
      si.memLayout(),
      si.diskLayout(),
      si.graphics(),
      si.osInfo(),
      si.networkInterfaces()
    ]);

    // Process GPU info
    const gpus = [];
    if (graphics.controllers && graphics.controllers.length > 0) {
      for (const gpu of graphics.controllers) {
        gpus.push({
          name: gpu.model,
          vram_mb: gpu.vram ? Math.round(gpu.vram) : 0,
          driver_version: gpu.driverVersion || null,
          vendor: gpu.vendor || null
        });
      }
    }

    // Process memory layout
    const memoryList = memLayout.map(mem => ({
      size: mem.size,
      size_gb: Math.round(mem.size / (1024 * 1024 * 1024) * 100) / 100,
      type: mem.type || 'Unknown',
      clockSpeed: mem.clockSpeed || null,
      manufacturer: mem.manufacturer || null,
      partNum: mem.partNum || null
    }));

    // Process disk info
    const disks = diskLayout.map(disk => ({
      name: disk.name,
      size: disk.size,
      size_tb: Math.round(disk.size / (1024 * 1024 * 1024 * 1024) * 100) / 100,
      type: disk.type || 'Unknown',
      interfaceType: disk.interfaceType || 'Unknown',
      vendor: disk.vendor || null,
      serialNum: disk.serialNum || null
    }));

    // Process network interfaces
    const network = [];
    for (const iface of networkInterfaces) {
      if (iface.ip4 && iface.mac && iface.mac !== '00:00:00:00:00:00') {
        network.push({
          name: iface.iface,
          ip4: iface.ip4,
          mac: iface.mac,
          type: iface.type || 'Unknown'
        });
      }
    }

    // Build result
    const result = {
      // CPU
      cpu: {
        manufacturer: cpu.manufacturer,
        brand: cpu.brand,
        cores: cpu.cores,
        physicalCores: cpu.physicalCores,
        speed: cpu.speed,
        speedMax: cpu.speedMax,
        speedMin: cpu.speedMin,
        currentSpeed: cpuCurrentSpeed.avg,
        currentSpeedMin: cpuCurrentSpeed.min,
        currentSpeedMax: cpuCurrentSpeed.max
      },
      
      // Memory
      memory: {
        total: memory.total,
        total_gb: Math.round(memory.total / (1024 * 1024 * 1024) * 100) / 100,
        used: memory.used,
        free: memory.free,
        active: memory.active,
        available: memory.available,
        usedPercent: Math.round(memory.usedPercent * 100) / 100,
        layout: memoryList
      },
      
      // GPU
      graphics: {
        gpus: gpus,
        displays: graphics.displays || []
      },
      
      // Disk
      disk: {
        layout: disks,
        totalSize: disks.reduce((sum, d) => sum + d.size, 0)
      },
      
      // OS
      os: {
        platform: osInfo.platform,
        distro: osInfo.distro,
        release: osInfo.release,
        arch: osInfo.arch,
        hostname: osInfo.hostname,
        kernel: osInfo.kernel,
        build: osInfo.build,
        edition: osInfo.edition,
        codename: osInfo.codename
      },
      
      // Network
      network: network,
      
      // System
      system: {
        manufacturer: osInfo.manufacturer,
        model: osInfo.model,
        uuid: osInfo.serial || null
      },
      
      // Timestamp
      timestamp: new Date().toISOString()
    };

    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Get GPU metrics from nvidia-smi (fallback when systeminformation fails)
 */
async function getNvidiaGpuMetrics() {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    exec('nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits', 
      { timeout: 5000 },
      (error, stdout, stderr) => {
        if (error) {
          resolve(null);
          return;
        }
        
        const parts = stdout.trim().split(',').map(s => parseFloat(s.trim()));
        if (parts.length >= 5 && !isNaN(parts[0])) {
          resolve({
            percent: parts[0],
            memory_percent: parts[1],
            memory_used_mb: parts[2],
            memory_total_mb: parts[3],
            temperature: parts[4]
          });
        } else {
          resolve(null);
        }
      }
    );
  });
}

async function getRealtimeMetrics() {
  try {
    // Get realtime metrics (CPU, memory, etc.)
    const cpuLoad = await si.currentLoad();
    const cpuCurrentSpeed = await si.cpuCurrentSpeed();
    const memory = await si.mem();
    const graphics = await si.graphics();
    const diskIO = await si.disksIO();
    const networkStats = await si.networkStats();
    
    // Get processes separately as it can be heavy
    let processes = { list: [] };
    try {
      // Limit to top 20 processes to save time
      processes = await si.processes();
    } catch (e) {
      // Ignore process error
    }

    // Process GPU info
    let gpuPercent = 0;
    let gpuMemoryUsed = 0;
    let gpuMemoryTotal = 0;
    let gpuTemperature = 0;

    if (graphics.controllers && graphics.controllers.length > 0) {
      const gpu = graphics.controllers[0];
      gpuPercent = gpu.utilizationGpu || 0;
      gpuMemoryUsed = gpu.memoryUsed || 0;
      gpuMemoryTotal = gpu.memoryTotal || 0;
      gpuTemperature = gpu.temperatureGpu || 0;
      
      // If VRAM is missing but we have vram from info
      if (!gpuMemoryTotal && gpu.vram) {
          gpuMemoryTotal = gpu.vram;
      }
    }

    // Disk IO (aggregate all disks)
    let read_sec = 0;
    let write_sec = 0;
    
    if (diskIO) {
        read_sec = diskIO.rIO_sec || 0;
        write_sec = diskIO.wIO_sec || 0;
    }

    // Network (aggregate all interfaces)
    let rx_sec = 0;
    let tx_sec = 0;
    
    if (networkStats && Array.isArray(networkStats)) {
        for (const iface of networkStats) {
            rx_sec += iface.rx_sec || 0;
            tx_sec += iface.tx_sec || 0;
        }
    } else if (networkStats) {
        rx_sec = networkStats.rx_sec || 0;
        tx_sec = networkStats.tx_sec || 0;
    }

    const result = {
      // CPU
      cpu: {
        percent: Math.round(cpuLoad.currentLoad * 100) / 100,
        speed: cpuCurrentSpeed.avg,
      },
      
      // Memory
      memory: {
        total: memory.total,
        used: memory.used,
        free: memory.free,
        available: memory.available,
        percent: Math.round((memory.used / memory.total) * 10000) / 100,
        used_mb: Math.round(memory.used / (1024 * 1024)),
        available_mb: Math.round(memory.available / (1024 * 1024))
      },
      
      // GPU
      gpu: {
        percent: gpuPercent,
        memory_used_mb: gpuMemoryUsed,
        memory_total_mb: gpuMemoryTotal,
        temperature: gpuTemperature
      },
      
      // Disk
      disk: {
        read_mbps: Math.round(read_sec / (1024 * 1024) * 100) / 100,
        write_mbps: Math.round(write_sec / (1024 * 1024) * 100) / 100
      },
      
      // Network
      network: {
        rx_mbps: Math.round(rx_sec / (1024 * 1024) * 100) / 100,
        tx_mbps: Math.round(tx_sec / (1024 * 1024) * 100) / 100
      },
      
      // Process list
      top_processes: processes.list
        .sort((a, b) => b.cpu - a.cpu)
        .slice(0, 10)
        .map(p => ({
          name: p.name,
          pid: p.pid,
          cpu: Math.round(p.cpu * 100) / 100,
          memory: Math.round(p.mem * 100) / 100,
          path: p.path || ''
        })),
      
      timestamp: new Date().toISOString()
    };

    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// CLI handling
const args = process.argv.slice(2);
const command = args[0] || 'info';

async function main() {
  let result;
  
  switch (command) {
    case 'metrics':
      result = await getRealtimeMetrics();
      break;
    case 'info':
    default:
      result = await getHardwareInfo();
      break;
  }
  
  console.log(JSON.stringify(result, null, 2));
}

main();
