import os
import sys
import requests
import logging
import subprocess
import time
from packaging import version

logger = logging.getLogger(__name__)

class GitHubUpdater:
    def __init__(self, owner, repo, current_version, asset_name="RoleFitAgent.exe"):
        self.owner = owner
        self.repo = repo
        self.current_version = current_version
        self.asset_name = asset_name
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    def check_for_updates(self):
        """检查是否有新版本"""
        try:
            logger.info(f"Checking for updates from {self.owner}/{self.repo}...")
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to check updates: {response.status_code}")
                return None

            data = response.json()
            latest_tag = data.get("tag_name", "v0.0.0").lstrip("v")
            
            # 版本比较
            if version.parse(latest_tag) > version.parse(self.current_version):
                logger.info(f"New version found: {latest_tag} (Current: {self.current_version})")
                return data
            else:
                logger.debug(f"Agent is up to date (Current: {self.current_version}, Latest: {latest_tag}).")
                return None
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return None

    def download_update(self, download_url, save_path):
        """下载新版本"""
        try:
            logger.info(f"Downloading update from {download_url}...")
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Download complete.")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def perform_update(self, release_data):
        """执行更新流程：下载 -> 重命名 -> 替换 -> 重启"""
        assets = release_data.get("assets", [])
        download_url = None
        
        # 找到对应的 EXE 资源
        for asset in assets:
            if asset["name"] == self.asset_name:
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            logger.error(f"Asset {self.asset_name} not found in release.")
            return False

        # 路径定义
        current_exe = sys.executable
        # 如果是在 IDE 或脚本运行，sys.executable 是 python.exe，这种情况下跳过更新
        if not getattr(sys, 'frozen', False):
            logger.warning("Running from source script, skipping self-update.")
            return False

        new_exe = current_exe + ".new"
        old_exe = current_exe + ".old"

        # 1. 下载新版
        if not self.download_update(download_url, new_exe):
            return False

        try:
            # 2. 重命名当前运行的 EXE (Windows 允许重命名运行中的文件)
            if os.path.exists(old_exe):
                try:
                    os.remove(old_exe) # 清理上次残留
                except:
                    pass
            
            logger.info(f"Renaming current EXE to {old_exe}...")
            os.rename(current_exe, old_exe)

            # 3. 将新下载的文件命名为原 EXE 名称
            logger.info(f"Applying new EXE to {current_exe}...")
            os.rename(new_exe, current_exe)

            # 4. 重启应用
            logger.info("Restarting application...")
            subprocess.Popen([current_exe] + sys.argv[1:])
            sys.exit(0) # 退出当前进程

        except Exception as e:
            logger.error(f"Update failed during file operations: {e}")
            # 尝试回滚
            if os.path.exists(old_exe) and not os.path.exists(current_exe):
                try:
                    os.rename(old_exe, current_exe)
                except:
                    pass
            return False
