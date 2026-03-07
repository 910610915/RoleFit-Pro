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
 * Get realtime metrics (CPU, memory, etc.)
 */
async function getRealtimeMetrics() {
  try {
    const [
      cpuLoad,
      cpuCurrentSpeed,
      memory,
      gpuLoad,
      gpuMemory,
      diskIO,
      networkIO
    ] = await Promise.all([
      si.currentLoad(),
      si.cpuCurrentSpeed(),
      si.mem(),
      si.graphics(),
      si.fsSize(),
      si.disksIO(),
      si.networkStats()
    ]);

    // Get GPU metrics
    let gpuPercent = null;
    let gpuMemoryUsed = null;
    let gpuMemoryTotal = null;
    let gpuTemperature = null;

    if (gpuLoad.controllers && gpuLoad.controllers.length > 0) {
      const gpu = gpuLoad.controllers[0];
      gpuPercent = gpu.utilizationGpu || null;
      gpuMemoryUsed = gpu.utilizationMemory ? Math.round(gpu.memoryUsed * 1024) : null; // Convert to MB
      gpuMemoryTotal = gpu.memoryTotal ? Math.round(gpu.memoryTotal * 1024) : null;
      gpuTemperature = gpu.temperatureGpu || null;
    }

    const result = {
      // CPU
      cpu: {
        percent: Math.round(cpuLoad.currentLoad * 100) / 100,
        speed: cpuCurrentSpeed.avg,
        cores: cpuLoad.cpus.map(c => Math.round(c.load * 100) / 100)
      },
      
      // Memory
      memory: {
        total: memory.total,
        total_gb: Math.round(memory.total / (1024 * 1024 * 1024) * 100) / 100,
        used: memory.used,
        free: memory.free,
        available: memory.available,
        percent: Math.round(memory.usedPercent * 100) / 100,
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
      
      // Disk (simplified)
      disk: {
        read_bytes: diskIO ? diskIO.rIO_sec : 0,
        write_bytes: diskIO ? diskIO.wIO_sec : 0,
        read_mbps: diskIO ? Math.round(diskIO.rIO_sec / (1024 * 1024) * 100) / 100 : 0,
        write_mbps: diskIO ? Math.round(diskIO.wIO_sec / (1024 * 1024) * 100) / 100 : 0
      },
      
      // Network (simplified)
      network: {
        rx_sec: networkIO ? networkIO.rx_sec : 0,
        tx_sec: networkIO ? networkIO.tx_sec : 0,
        rx_mbps: networkIO ? Math.round(networkIO.rx_sec / (1024 * 1024) * 100) / 100 : 0,
        tx_mbps: networkIO ? Math.round(networkIO.tx_sec / (1024 * 1024) * 100) / 100 : 0
      },
      
      // Process count
      processes: os.loadavg(), // Just for reference
      
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
