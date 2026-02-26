# RoleFit Pro 一键安装
# 复制以下命令到 PowerShell 中执行：

powershell -ExecutionPolicy Bypass -Command "
Write-Host 'RoleFit Pro 一键部署...' -ForegroundColor Cyan

# 检查Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host '安装Python...' -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    \$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
}

Write-Host 'Python:' (python --version)

# 克隆/更新代码
\$repoUrl = 'https://github.com/910610915/RoleFit-Pro.git'
\$installDir = Join-Path \$env:USERPROFILE 'RoleFitPro'

if (!(Test-Path \$installDir)) {
    git clone \$repoUrl \$installDir
} else {
    Write-Host '代码已存在，跳过克隆'
}

# 安装后端
Set-Location (Join-Path \$installDir 'backend')
pip install -r requirements.txt --quiet

# 初始化
python init_sqlite.py

# 启动
Write-Host '启动服务...' -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"
