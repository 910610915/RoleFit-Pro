#!/usr/bin/env node
/**
 * Hardware Info - Using systeminformation library
 * Provides accurate hardware information for Windows
 */

const si = require('systeminformation');
const os = require('os');
const { exec } = require('child_process');

/**
 * Get CPU temperature via WMI (Windows only)
 * Requires OpenHardwareMonitor or similar tool running
 */
function getCPUTemperatureWMI() {
  return new Promise((resolve) => {
    if (process.platform !== 'win32') {
      resolve(null);
      return;
    }
    
    // Try using PowerShell to query WMI for temperature
    // This works with OpenHardwareMonitor or other hardware monitoring tools
    const psCmd = `powershell -Command "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty CurrentTemperature"`;
    
    exec(psCmd, { timeout: 5000 }, (error, stdout, stderr) => {
      if (error || !stdout.trim()) {
        // Try alternative: query via wmic
        exec('wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature /value', 
          { timeout: 5000 }, 
          (err2, stdout2, stderr2) => {
            if (err2 || !stdout2.trim()) {
              resolve(null);
              return;
            }
            try {
              // Parse temperature from output like "CurrentTemperature=300"
              const match = stdout2.match(/CurrentTemperature=(\d+)/i);
              if (match && match[1]) {
                // WMI returns temperature in tenths of Kelvin
                const tempK = parseInt(match[1]) / 10;
                const tempC = tempK - 273.15;
                resolve(Math.round(tempC * 10) / 10);
              } else {
                resolve(null);
              }
            } catch (e) {
              resolve(null);
            }
          }
        );
        return;
      }
      
      try {
        // PowerShell returns temperature in Kelvin
        const tempK = parseFloat(stdout.trim());
        if (tempK > 0) {
          const tempC = tempK - 273.15;
          resolve(Math.round(tempC * 10) / 10);
        } else {
          resolve(null);
        }
      } catch (e) {
        resolve(null);
      }
    });
  });
}

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
function getNvidiaGpuMetrics() {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    // Query: utilization.gpu (%), utilization.memory (%), memory.used (MiB), memory.total (MiB), temperature.gpu (C)
    exec('nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits', 
      { timeout: 5000 },
      (error, stdout, stderr) => {
        if (error) {
          resolve(null);
          return;
        }
        
        try {
          // Get first line (first GPU) and clean up
          const firstLine = stdout.trim().split('\n')[0];
          // Split by comma and clean each part - remove % sign, MiB, etc.
          const parts = firstLine.split(',').map(s => {
            const cleaned = s.trim()
              .replace(/%/g, '')
              .replace(/MiB/g, '')
              .replace(/Mi/g, '')
              .replace(/GiB/g, '')
              .replace(/Gi/g, '')
              .replace(/W/i, '')
              .replace(/MHz/g, '')
              .trim();
            return parseFloat(cleaned);
          });
          
          if (parts.length >= 5 && !isNaN(parts[0]) && parts[0] >= 0 && parts[0] <= 100) {
            resolve({
              percent: parts[0],
              memory_percent: parts[1],
              memory_used_mb: parts[2],
              memory_total_mb: parts[3],
              temperature: parts[4]
            });
          } else {
            // Try alternative parsing for different nvidia-smi versions
            const nums = firstLine.match(/[\d.]+/g);
            if (nums && nums.length >= 5) {
              resolve({
                percent: parseFloat(nums[0]),
                memory_percent: parseFloat(nums[1]),
                memory_used_mb: parseFloat(nums[2]),
                memory_total_mb: parseFloat(nums[3]),
                temperature: parseFloat(nums[4])
              });
            } else {
              resolve(null);
            }
          }
        } catch (e) {
          resolve(null);
        }
      }
    );
  });
}

function getDiskCounters() {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    // Counters: Queue Length, Latency (sec/Transfer), Read Bytes/sec, Write Bytes/sec
    const cmd = 'typeperf "\\PhysicalDisk(*)\\Current Disk Queue Length" "\\PhysicalDisk(*)\\Avg. Disk sec/Transfer" "\\PhysicalDisk(*)\\Disk Read Bytes/sec" "\\PhysicalDisk(*)\\Disk Write Bytes/sec" -sc 1';
    
    exec(cmd, { timeout: 5000 }, (error, stdout, stderr) => {
      if (error || !stdout) {
        resolve([]);
        return;
      }

      try {
        const lines = stdout.trim().split('\n');
        // Find header line (starts with "(PDH-CSV")
        let headerIndex = -1;
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('"(PDH-CSV')) {
            headerIndex = i;
            break;
          }
        }

        if (headerIndex === -1 || headerIndex + 1 >= lines.length) {
          resolve([]);
          return;
        }

        // Parse header to map columns
        const headerLine = lines[headerIndex];
        const valueLine = lines[headerIndex + 1];
        
        // Split by comma, handling quotes
        const headers = headerLine.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g).map(s => s.replace(/^"|"$/g, ''));
        const values = valueLine.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g).map(s => s.replace(/^"|"$/g, ''));

        const diskMap = {};

        // Start from index 1 (0 is timestamp)
        for (let i = 1; i < headers.length; i++) {
          const header = headers[i];
          const value = parseFloat(values[i]);
          
          if (isNaN(value)) continue;

          // Parse header: \\Hostname\PhysicalDisk(Instance)\Counter
          const match = header.match(/\\PhysicalDisk\((.*?)\)\\(.*)/);
          if (match) {
            const instance = match[1]; // e.g. "0 C:" or "_Total"
            const counter = match[2]; // e.g. "Current Disk Queue Length"

            if (!diskMap[instance]) {
              diskMap[instance] = { name: instance };
            }

            if (counter.includes('Queue Length')) {
              diskMap[instance].queue_length = value;
            } else if (counter.includes('sec/Transfer')) {
              diskMap[instance].latency_ms = value * 1000; // Convert sec to ms
            } else if (counter.includes('Read Bytes/sec')) {
              diskMap[instance].read_bytes_sec = value;
            } else if (counter.includes('Write Bytes/sec')) {
              diskMap[instance].write_bytes_sec = value;
            }
          }
        }

        // Convert map to array
        const result = Object.values(diskMap);
        resolve(result);

      } catch (e) {
        resolve([]);
      }
    });
  });
}

async function getRealtimeMetrics() {
  try {
    // Get realtime metrics (CPU, memory, etc.)
    const cpuLoad = await si.currentLoad();
    const cpuCurrentSpeed = await si.cpuCurrentSpeed();
    let cpuTemp = await si.cpuTemperature();
    const memory = await si.mem();
    const graphics = await si.graphics();
    const diskIO = await si.disksIO();
    const networkStats = await si.networkStats();
    
    // If cpuTemp is null/undefined (common on Windows), try WMI fallback
    if (!cpuTemp || cpuTemp.main === null || cpuTemp.main === undefined) {
      const wmiTemp = await getCPUTemperatureWMI();
      if (wmiTemp !== null) {
        cpuTemp = { main: wmiTemp };
      }
    }
    
    // Get detailed disk counters (Windows only)
    let diskDetails = [];
    if (process.platform === 'win32') {
        diskDetails = await getDiskCounters();
    }
    
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

    // Try to get from systeminformation first
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

    // If si failed to get usage (which is common on Windows), try nvidia-smi
    if (gpuPercent === 0) {
      const nvidiaMetrics = await getNvidiaGpuMetrics();
      if (nvidiaMetrics) {
        gpuPercent = nvidiaMetrics.percent;
        gpuTemperature = nvidiaMetrics.temperature;
        gpuMemoryUsed = nvidiaMetrics.memory_used_mb;
        gpuMemoryTotal = nvidiaMetrics.memory_total_mb;
      }
    }

    // Disk IO (aggregate all disks)
    // We return TOTAL bytes here, and let the Python agent calculate the rate
    let read_bytes = 0;
    let write_bytes = 0;
    
    if (diskIO) {
        read_bytes = diskIO.rIO || 0;
        write_bytes = diskIO.wIO || 0;
    } else {
        // Fallback: try fsStats if disksIO fails (sometimes better on Windows)
        try {
            const fsStats = await si.fsStats();
            if (fsStats) {
                read_bytes = fsStats.rx || 0;
                write_bytes = fsStats.wx || 0;
            }
        } catch (e) {
            // Ignore
        }
    }

    // Network (aggregate all interfaces)
    let rx_bytes = 0;
    let tx_bytes = 0;
    
    if (networkStats && Array.isArray(networkStats)) {
        for (const iface of networkStats) {
            rx_bytes += iface.rx_bytes || 0;
            tx_bytes += iface.tx_bytes || 0;
        }
    } else if (networkStats) {
        rx_bytes = networkStats.rx_bytes || 0;
        tx_bytes = networkStats.tx_bytes || 0;
    }

    const result = {
      // CPU
      cpu: {
        percent: Math.round(cpuLoad.currentLoad * 100) / 100,
        speed: cpuCurrentSpeed.avg,
        temperature: cpuTemp ? cpuTemp.main : null,
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
      
      // Disk (Raw counters)
      disk: {
        read_bytes: read_bytes,
        write_bytes: write_bytes,
        details: diskDetails
      },
      
      // Network (Raw counters)
      network: {
        rx_bytes: rx_bytes,
        tx_bytes: tx_bytes
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
