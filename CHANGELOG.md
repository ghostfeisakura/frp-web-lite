# 更新日志 Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-07-30

### ✨ 新增 Added
- 🚀 轻量级FRP Web控制面板
- ⚡ 一键安装脚本 (`install.sh`)
- 🔧 frps服务管理功能（启动/停止/重启）
- 📊 实时状态监控和日志查看
- 🛡️ 资源监控守护进程 (`resource_guardian.py`)
- 📱 响应式Web界面设计
- 🔐 简单的登录验证系统

### 🎯 优化 Optimized
- 💾 内存使用优化：< 400MB
- ⚡ CPU使用限制：150% (1.5核)
- 📦 最小依赖：仅Flask + psutil
- 🗜️ 前端资源内联，零外部依赖
- 🔄 智能缓存机制减少系统调用

### 🛡️ 安全 Security
- 🔒 最小权限sudo配置
- 🏠 专用用户运行服务
- 🛡️ systemd安全限制
- 📝 详细的操作日志记录

### 📋 技术规格 Technical Specs
- **目标环境**: 2核0.5GB RAM轻量云服务器
- **内存限制**: 400MB硬限制，350MB软限制
- **支持系统**: Ubuntu 18.04+, Debian 9+
- **Python版本**: 3.6+
- **Web框架**: Flask 2.3.3

### 📁 项目结构 Project Structure
```
frp-web-lite/
├── app.py                    # 主应用程序
├── requirements.txt          # Python依赖
├── install.sh               # 一键安装脚本
├── frp-web.service          # systemd服务配置
├── resource_guardian.py     # 资源监控守护进程
├── performance_monitor.py   # 性能监控工具
├── sudoers-frp-web         # sudo权限配置
├── templates/
│   ├── index.html          # 主控制面板
│   └── login.html          # 登录页面
└── README.md               # 项目文档
```

### 🎯 性能指标 Performance Metrics
- **内存使用**: 50-80MB (目标 < 400MB)
- **启动时间**: 1-2秒
- **响应时间**: < 2秒
- **可用性**: > 99%

---

## 计划中的功能 Planned Features

### [1.1.0] - 计划中
- [ ] 📈 更详细的性能图表
- [ ] 🔔 邮件/webhook通知
- [ ] 🌐 多语言支持
- [ ] 📱 PWA支持
- [ ] 🔧 配置文件在线编辑

### [1.2.0] - 计划中
- [ ] 👥 多用户支持
- [ ] 🔐 HTTPS自动配置
- [ ] 📊 历史数据存储
- [ ] 🔄 自动备份功能
- [ ] 🐳 Docker一键部署

---

## 贡献指南 Contributing

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone https://github.com/ghostfeisakura/frp-web-lite.git
cd frp-web-lite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动
