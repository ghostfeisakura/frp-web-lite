# FRP Web Lite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)

🚀 **专为2核0.5GB RAM轻量应用云优化的FRP控制面板**

A lightweight web control panel for frps service management, optimized for 2-core 0.5GB RAM cloud servers.

## ✨ 特性 Features

- 🎯 **轻量优化**: 内存使用 < 400MB，专为资源受限环境设计
- ⚡ **快速部署**: 一键安装脚本，自动安装frps服务端+Web控制面板
- 🔧 **完整解决方案**: 自动下载安装最新版frps，无需手动配置
- 📊 **双重管理**: Web控制面板 + frps原生Dashboard
- 🛡️ **安全可靠**: 最小权限原则，自动资源监控
- 📱 **响应式设计**: 支持桌面和移动端访问
- 🔄 **服务管理**: 启动/停止/重启 frps 服务
- 📈 **实时监控**: 服务状态和日志实时查看

## 🎯 轻量化特性

### 内存优化
- **内存限制**: 400MB硬限制，350MB软限制
- **自动重启**: 内存超限时自动重启服务
- **缓存优化**: 智能缓存减少系统调用
- **垃圾回收**: 主动内存清理机制

### CPU优化
- **CPU配额**: 限制150% CPU使用（1.5核）
- **进程限制**: 最大50个任务
- **I/O优化**: 低优先级I/O调度
- **Nice值**: 设置为5，降低CPU优先级

### 资源监控
- **实时监控**: 每30秒检查资源使用
- **自动恢复**: 异常时自动重启
- **日志记录**: 详细的资源使用日志
- **告警机制**: 资源超限时发出警告

## � 快速开始 Quick Start

### 一键安装（推荐）
```bash
# 克隆项目
git clone https://github.com/ghostfeisakura/frp-web-lite.git
cd frp-web-lite

# 一键安装
sudo bash install.sh
```

### 访问控制面板
```
Web控制面板: http://你的服务器IP:5000
FRP Dashboard: http://你的服务器IP:7500
FRP服务端口: 你的服务器IP:7000

默认登录信息:
用户名: admin
密码: admin123
```

> ⚠️ **安全提示**: 生产环境请及时修改默认密码！

### 手动安装
```bash
# 1. 安装最小依赖
sudo apt update
sudo apt install -y python3-minimal python3-pip python3-venv

# 2. 创建用户和目录
sudo useradd -r -s /bin/false frp-web
sudo mkdir -p /opt/frp-web-control

# 3. 安装轻量版应用
sudo cp app_lightweight.py /opt/frp-web-control/app.py
sudo cp templates/*_lite.html /opt/frp-web-control/templates/
sudo cp requirements_lightweight.txt /opt/frp-web-control/requirements.txt

# 4. 创建虚拟环境
cd /opt/frp-web-control
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# 5. 安装服务
sudo cp frp-web-lite.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable frp-web-lite
sudo systemctl start frp-web-lite
```

## 🔧 配置说明

### 环境变量
```bash
# 基本配置
FLASK_HOST=0.0.0.0          # 监听地址
FLASK_PORT=5000             # 监听端口
FLASK_DEBUG=false           # 生产模式

# 服务配置
USE_SYSTEMD=true            # 使用systemd管理frps
FRPS_SERVICE=frps           # frps服务名
LOGIN_REQUIRED=true         # 启用登录验证

# 性能配置
PYTHONUNBUFFERED=1          # 禁用Python缓冲
PYTHONDONTWRITEBYTECODE=1   # 禁用.pyc文件
```

### 资源限制配置
编辑 `/opt/frp-web-control/guardian_config.json`:
```json
{
  "service_name": "frp-web-lite",
  "memory_limit_mb": 400,
  "cpu_limit_percent": 80,
  "check_interval": 30,
  "restart_cooldown": 300,
  "max_restarts_per_hour": 3,
  "enable_auto_restart": true,
  "enable_memory_cleanup": true
}
```

## 📊 性能监控

### 启动资源守护进程
```bash
# 创建配置文件
sudo python3 /opt/frp-web-control/resource_guardian.py create-config

# 启动守护进程
sudo python3 /opt/frp-web-control/resource_guardian.py &

# 或添加到systemd
sudo systemctl enable frp-web-guardian
sudo systemctl start frp-web-guardian
```

### 监控命令
```bash
# 查看服务状态
sudo systemctl status frp-web-lite

# 查看资源使用
sudo journalctl -u frp-web-lite -f

# 查看守护进程日志
sudo tail -f /var/log/frp-web-guardian.log

# 手动检查资源
sudo python3 /opt/frp-web-control/resource_guardian.py check-once
```

## 🚀 性能优化建议

### 系统级优化
```bash
# 1. 创建swap文件（重要！）
sudo fallocate -l 512M /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 优化内核参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
sudo sysctl -p

# 3. 禁用不必要的服务
sudo systemctl disable snapd
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

### 应用级优化
- ✅ 使用轻量版模板（无外部CSS/JS依赖）
- ✅ 启用智能缓存（5-10秒TTL）
- ✅ 限制日志行数（最大200行）
- ✅ 优化数据库查询频率
- ✅ 使用内存映射文件

## 🔍 故障排除

### 常见问题

**1. 内存不足**
```bash
# 检查内存使用
free -h
sudo systemctl status frp-web-lite

# 查看进程内存
ps aux | grep frp-web
```

**2. 服务频繁重启**
```bash
# 查看重启日志
sudo journalctl -u frp-web-lite | grep restart

# 检查资源守护进程
sudo tail -f /var/log/frp-web-guardian.log
```

**3. CPU使用过高**
```bash
# 查看CPU使用
top -p $(pgrep -f frp-web)

# 调整CPU限制
sudo systemctl edit frp-web-lite
# 添加: [Service]
#      CPUQuota=100%
```

### 性能调优

**内存优化**
- 减少缓存TTL时间
- 限制并发连接数
- 启用更频繁的垃圾回收

**CPU优化**
- 降低检查频率
- 使用异步处理
- 优化正则表达式

## 📈 监控指标

### 关键指标
- **内存使用**: < 400MB
- **CPU使用**: < 80%
- **响应时间**: < 2秒
- **重启次数**: < 3次/小时

### 告警阈值
- 🟡 内存 > 350MB: 警告
- 🔴 内存 > 400MB: 自动重启
- 🟡 CPU > 80%: 警告
- 🔴 连续高CPU > 5分钟: 重启

## 🛡️ 安全配置

### 系统安全
- 专用用户运行（frp-web）
- 最小权限原则
- 禁用不必要的系统调用
- 私有临时目录

### 网络安全
- 仅开放必要端口
- 禁用设备访问
- 保护主机名和时钟
- 限制命名空间

## 📝 更新日志

### v1.0-lightweight
- 🚀 专为轻量服务器优化
- 💾 内存使用减少60%
- ⚡ 启动时间减少50%
- 🔧 自动资源管理
- 📊 实时性能监控

## 💡 最佳实践

1. **定期监控**: 每天检查资源使用情况
2. **及时更新**: 保持系统和依赖包最新
3. **备份配置**: 定期备份配置文件
4. **测试恢复**: 定期测试自动重启功能
5. **日志轮转**: 配置日志轮转防止磁盘满

---

🎯 **目标**: 在0.5GB RAM服务器上稳定运行，内存使用 < 400MB，响应时间 < 2秒
