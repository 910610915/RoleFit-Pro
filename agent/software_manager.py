# Software Manager for Hardware Benchmark Agent
# Handles software download, installation, and detection on target machines

import os
import sys
import json
import logging
import subprocess
import requests
import zipfile
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoftwareManager:
    """Agent端软件管理器 - 负责软件的下载、安装和检测"""
    
    # 默认安装路径
    DEFAULT_INSTALL_PATH = r"C:\Program Files (x86)\BenchmarkTools"
    
    def __init__(self, server_url: str, temp_dir: str = None):
        self.server_url = server_url
        self.temp_dir = temp_dir or os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'benchmark_software')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 7-Zip 路径
        self.sevenzip_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe"
        ]
        self.sevenzip = self._find_7zip()
    
    def _find_7zip(self) -> Optional[str]:
        """查找系统中的7-Zip"""
        for path in self.sevenzip_paths:
            if os.path.exists(path):
                return path
        return None
    
    # ====== 1. 检测软件是否已安装 ======
    
    def check_installed(self, software: Dict[str, Any]) -> bool:
        """检测软件是否已安装"""
        method = software.get('detection_method', 'file')
        keyword = software.get('detection_keyword', '')
        path = software.get('detection_path', '')
        
        logger.info(f"Checking if {software.get('software_name')} is installed (method: {method})")
        
        if method == 'file':
            return self._check_file(path)
        elif method == 'process':
            return self._check_process(keyword)
        elif method == 'registry':
            return self._check_registry(keyword)
        else:
            logger.warning(f"Unknown detection method: {method}")
            return False
    
    def _check_file(self, path: str) -> bool:
        """检测文件/目录是否存在"""
        if not path:
            return False
        exists = os.path.exists(path)
        logger.info(f"File check: {path} -> {exists}")
        return exists
    
    def _check_process(self, keyword: str) -> bool:
        """检测进程是否运行"""
        if not keyword:
            return False
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {keyword}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            found = keyword.lower() in result.stdout.lower()
            logger.info(f"Process check: {keyword} -> {found}")
            return found
        except Exception as e:
            logger.error(f"Process check failed: {e}")
            return False
    
    def _check_registry(self, key: str) -> bool:
        """检测注册表项是否存在"""
        if not key:
            return False
        try:
            # 尝试打开注册表项
            import winreg
            parts = key.split('\\', 1)
            if len(parts) != 2:
                return False
            
            root, subkey = parts[0], parts[1]
            root_map = {
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKCU': winreg.HKEY_CURRENT_USER,
            }
            
            hkey = root_map.get(root.upper())
            if not hkey:
                return False
            
            try:
                with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ):
                    logger.info(f"Registry check: {key} -> True")
                    return True
            except FileNotFoundError:
                logger.info(f"Registry check: {key} -> False")
                return False
        except Exception as e:
            logger.error(f"Registry check failed: {e}")
            return False
    
    # ====== 2. 下载软件 ======
    
    def download(self, software_code: str) -> Optional[str]:
        """从服务器下载软件包"""
        url = f"{self.server_url}/api/software/download/{software_code}"
        
        logger.info(f"Downloading {software_code} from {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=7200)  # 2小时超时（大文件）
            response.raise_for_status()
            
            # 获取文件名
            content_disposition = response.headers.get('content-disposition', '')
            filename = self._extract_filename(content_disposition, software_code)
            
            filepath = os.path.join(self.temp_dir, filename)
            
            # 流式下载（支持大文件）
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 每10MB打印一次进度
                        if downloaded % (10*1024*1024) == 0:
                            logger.info(f"Downloaded {downloaded/(1024*1024):.1f} MB...")
            
            file_size = os.path.getsize(filepath) / (1024*1024)
            logger.info(f"Downloaded {software_code}: {file_size:.1f} MB")
            
            return filepath
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Software package not found on server: {software_code}")
            else:
                logger.error(f"HTTP error downloading {software_code}: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Download timeout for {software_code}")
            return None
        except Exception as e:
            logger.error(f"Download failed for {software_code}: {e}")
            return None
    
    def _extract_filename(self, content_disposition: str, default: str) -> str:
        """从 Content-Disposition 头提取文件名"""
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            return filename
        return f"{default}_package"
    
    # ====== 3. 安装/解压软件 ======
    
    def install(self, package_path: str, software: Dict[str, Any]) -> Dict[str, Any]:
        """安装或解压软件"""
        if not package_path or not os.path.exists(package_path):
            return {'success': False, 'error': 'Package file not found'}
        
        format_type = (software.get('package_format') or 'zip').lower()
        target_path = software.get('target_install_path', self.DEFAULT_INSTALL_PATH)
        subfolder = software.get('subfolder_name', '')
        
        # 构建目标路径
        if subfolder:
            target_path = os.path.join(target_path, subfolder)
        
        logger.info(f"Installing {software.get('software_name')} to {target_path}")
        logger.info(f"Package format: {format_type}")
        
        try:
            if format_type in ['zip']:
                return self._extract_zip(package_path, target_path)
            elif format_type in ['rar']:
                return self._extract_rar(package_path, target_path)
            elif format_type in ['7z']:
                return self._extract_7z(package_path, target_path)
            elif format_type in ['exe', 'msi']:
                return self._install_exe_msi(package_path, software)
            else:
                return {'success': False, 'error': f'Unsupported format: {format_type}'}
        except Exception as e:
            logger.error(f"Install failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_zip(self, archive: str, target: str) -> Dict[str, Any]:
        """解压 ZIP"""
        try:
            os.makedirs(target, exist_ok=True)
            with zipfile.ZipFile(archive, 'r') as zf:
                zf.extractall(target)
            
            # 查找解压后的主程序
            exe_path = self._find_exe_in_dir(target)
            
            logger.info(f"Extracted ZIP to {target}")
            return {
                'success': True, 
                'installed_path': target,
                'exe_path': exe_path
            }
        except Exception as e:
            return {'success': False, 'error': f'ZIP extraction failed: {e}'}
    
    def _extract_rar(self, archive: str, target: str) -> Dict[str, Any]:
        """解压 RAR"""
        # 检查系统是否安装了 WinRAR
        winrar_paths = [
            r"C:\Program Files\WinRAR\winrar.exe",
            r"C:\Program Files (x86)\WinRAR\winrar.exe"
        ]
        
        winrar = None
        for path in winrar_paths:
            if os.path.exists(path):
                winrar = path
                break
        
        if not winrar:
            return {'success': False, 'error': 'WinRAR not found on system'}
        
        try:
            os.makedirs(target, exist_ok=True)
            result = subprocess.run(
                [winrar, 'x', '-y', archive, target],
                capture_output=True,
                timeout=600
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': f'RAR extraction failed: {result.stderr.decode()}'}
            
            exe_path = self._find_exe_in_dir(target)
            
            logger.info(f"Extracted RAR to {target}")
            return {
                'success': True, 
                'installed_path': target,
                'exe_path': exe_path
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'RAR extraction timeout'}
        except Exception as e:
            return {'success': False, 'error': f'RAR extraction failed: {e}'}
    
    def _extract_7z(self, archive: str, target: str) -> Dict[str, Any]:
        """解压 7z"""
        if not self.sevenzip:
            return {'success': False, 'error': '7-Zip not found on system'}
        
        try:
            os.makedirs(target, exist_ok=True)
            result = subprocess.run(
                [self.sevenzip, 'x', '-y', '-o' + target, archive],
                capture_output=True,
                timeout=600
            )
            
            if result.returncode != 0:
                return {'success': False, 'error': f'7z extraction failed: {result.stderr.decode()}'}
            
            exe_path = self._find_exe_in_dir(target)
            
            logger.info(f"Extracted 7z to {target}")
            return {
                'success': True, 
                'installed_path': target,
                'exe_path': exe_path
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '7z extraction timeout'}
        except Exception as e:
            return {'success': False, 'error': f'7z extraction failed: {e}'}
    
    def _install_exe_msi(self, package: str, software: Dict[str, Any]) -> Dict[str, Any]:
        """静默安装 EXE/MSI"""
        cmd = software.get('silent_install_cmd', '')
        
        try:
            if package.lower().endswith('.msi'):
                install_cmd = f'msiexec /i "{package}" /qn'
                if cmd:
                    install_cmd += f' {cmd}'
            else:
                install_cmd = f'"{package}"'
                if cmd:
                    install_cmd += f' {cmd}'
            
            logger.info(f"Running: {install_cmd}")
            
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('gbk', errors='ignore') or result.stdout.decode('gbk', errors='ignore')
                return {'success': False, 'error': f'Install failed: {error_msg}'}
            
            # 安装成功后，检测安装路径
            target_path = software.get('target_install_path', self.DEFAULT_INSTALL_PATH)
            subfolder = software.get('subfolder_name', '')
            
            if subfolder:
                target_path = os.path.join(target_path, subfolder)
            
            exe_path = self._find_exe_in_dir(target_path)
            if not exe_path:
                # 尝试从 main_exe_relative_path 获取
                exe_rel = software.get('main_exe_relative_path', '')
                if exe_rel:
                    exe_path = os.path.join(target_path, exe_rel)
            
            return {
                'success': True,
                'installed_path': target_path,
                'exe_path': exe_path
            }
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Installation timeout'}
        except Exception as e:
            return {'success': False, 'error': f'Installation failed: {e}'}
    
    def _find_exe_in_dir(self, directory: str) -> Optional[str]:
        """在目录中查找 exe 文件"""
        if not os.path.exists(directory):
            return None
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_path = os.path.join(root, file)
                    logger.info(f"Found executable: {exe_path}")
                    return exe_path
        return None
    
    # ====== 4. 获取软件启动路径 ======
    
    def get_software_exe_path(self, software: Dict[str, Any]) -> Optional[str]:
        """获取软件可执行文件路径"""
        # 优先使用 detection_path
        detection_path = software.get('detection_path', '')
        if detection_path and os.path.exists(detection_path):
            if detection_path.endswith('.exe'):
                return detection_path
            else:
                # 是目录，查找 exe
                return self._find_exe_in_dir(detection_path)
        
        # 使用 target_install_path + main_exe_relative_path
        target_path = software.get('target_install_path', self.DEFAULT_INSTALL_PATH)
        subfolder = software.get('subfolder_name', '')
        exe_rel = software.get('main_exe_relative_path', '')
        
        if subfolder:
            target_path = os.path.join(target_path, subfolder)
        
        if exe_rel:
            exe_path = os.path.join(target_path, exe_rel)
            if os.path.exists(exe_path):
                return exe_path
        
        # 尝试在目标目录查找
        return self._find_exe_in_dir(target_path)
    
    # ====== 5. 清理临时文件 ======
    
    def cleanup_temp(self):
        """清理临时下载文件"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
                logger.info("Temp directory cleaned")
        except Exception as e:
            logger.error(f"Failed to clean temp directory: {e}")


# 测试代码
if __name__ == '__main__':
    # 测试检测功能
    manager = SoftwareManager('http://localhost:8000')
    
    # 测试文件检测
    test_software = {
        'software_name': 'Test Software',
        'detection_method': 'file',
        'detection_path': r'C:\Windows\notepad.exe'
    }
    
    result = manager.check_installed(test_software)
    print(f"Detection result: {result}")
