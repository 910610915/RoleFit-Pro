import subprocess
import platform
import wmi

def get_cpu_info():
    c = wmi.WMI()
    cpu = c.Win32_Processor()[0]
    return {
        'name': cpu.Name,
        'cores': cpu.NumberOfCores,
        'threads': cpu.NumberOfLogicalProcessors
    }

def get_memory_info():
    c = wmi.WMI()
    memory = c.Win32_PhysicalMemory()
    total_memory = sum(int(m.Capacity) for m in memory)
    return {
        'total_gb': round(total_memory / (1024**3), 2)
    }

def get_gpu_info():
    c = wmi.WMI()
    gpus = c.Win32_VideoController()
    gpu_info = []
    
    for gpu in gpus:
        vram_gb = None
        
        if 'NVIDIA' in gpu.Name:
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if result.returncode == 0:
                    vram_mib = int(result.stdout.strip().split('\n')[0])
                    vram_gb = round(vram_mib / 1024, 2)
            except:
                pass
        
        if vram_gb is None:
            if gpu.AdapterRAM:
                vram_gb = round(gpu.AdapterRAM / (1024**3), 2)
            else:
                vram_gb = 0.0
        
        gpu_info.append({
            'name': gpu.Name,
            'vram_gb': vram_gb
        })
    
    return gpu_info

def get_disk_info():
    c = wmi.WMI()
    disks = c.Win32_DiskDrive()
    disk_info = []
    
    for disk in disks:
        size_gb = round(int(disk.Size) / (1024**3), 2) if disk.Size else 0
        interface = disk.Description
        disk_info.append({
            'model': disk.Model,
            'interface': interface,
            'size_gb': size_gb
        })
    
    return disk_info

def get_os_info():
    return {
        'name': platform.system(),
        'version': platform.version()
    }

def generate_report():
    cpu = get_cpu_info()
    memory = get_memory_info()
    gpus = get_gpu_info()
    disks = get_disk_info()
    os_info = get_os_info()
    
    report = []
    report.append('=' * 50)
    report.append('电脑硬件体检报告')
    report.append('=' * 50)
    report.append(f'处理器 (CPU): {cpu["name"]}')
    report.append(f'物理核心数: {cpu["cores"]}')
    report.append(f'逻辑核心数: {cpu["threads"]}')
    report.append(f'总内存 (RAM): {memory["total_gb"]}GB')
    report.append('显卡信息:')
    for gpu in gpus:
        report.append(f'  - {gpu["name"]} (显存: {gpu["vram_gb"]}GB)')
    report.append('\n磁盘信息:')
    for disk in disks:
        report.append(f'  - {disk["model"]}')
        report.append(f'    接口: {disk["interface"]}')
        report.append(f'    容量: {disk["size_gb"]}GB')
    report.append(f'\n操作系统: {os_info["name"]} {os_info["version"]}')
    
    return '\n'.join(report)

if __name__ == '__main__':
    report = generate_report()
    print(report)
    
    with open('hardware_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
