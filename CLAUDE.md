# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个5E对战平台CS:GO比赛数据抓取和分析系统，包含数据抓取、API服务和前端展示功能。

## 核心架构

### 数据层
- **MySQL数据库**: 存储比赛数据、玩家统计、自定义比赛等信息
- **主要数据表**:
  - `matches` - 比赛基本信息
  - `match_player_stats` - 玩家比赛统计
  - `players` - 玩家基本信息
  - `custom_tournaments` - 自定义比赛管理

### 服务层
- **数据抓取调度器** (`scheduler.py`): 定时执行数据抓取任务
- **API服务器** (`api_server.py`): Flask RESTful API，提供数据查询接口
- **数据抓取模块**:
  - `incremental_fetch.py` - 增量数据抓取
  - `fetch_match_details_optimized.py` - 比赛详情抓取

### 前端层
- **React仪表板**: 位于 `csgo-dashboard/` 目录
- **静态HTML页面**: 比赛数据展示页面

## 常用开发命令

### 环境管理
```bash
# 安装Python依赖
pip install -r requirements.txt

# 创建虚拟环境（首次运行）
python3 -m venv venv
source venv/bin/activate
```

### 数据抓取
```bash
# 启动定时数据抓取调度器
./start_scheduler.sh

# 停止调度器
./stop_scheduler.sh

# 手动执行单次抓取
python incremental_fetch.py

# 抓取比赛详情
python fetch_match_details_optimized.py
```

### API服务
```bash
# 启动API服务器
./csgo_api_service.sh start

# 停止API服务器
./csgo_api_service.sh stop

# 重启API服务器
./csgo_api_service.sh restart

# 查看服务状态
./csgo_api_service.sh status

# 查看日志
./csgo_api_service.sh logs
```

### 前端构建
```bash
# 构建前端项目（需要先进入csgo-dashboard目录）
cd csgo-dashboard
npm install
npm run build

# 或使用构建脚本
./build_frontend.sh
```

## 数据库配置

数据库连接配置在 `api_server.py` 中的 `get_database_connection()` 函数：
- 默认主机: `106.14.121.148`
- 数据库: `cs_match_data`
- 环境变量支持: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

## API接口说明

### 核心接口
- `GET /api/players` - 玩家数据列表（支持分页、搜索、筛选）
- `GET /api/player/<steam_id>` - 单个玩家详情
- `GET /api/player/<steam_id>/stats` - 玩家历史统计
- `GET /api/matches` - 比赛列表
- `GET /api/match/<match_id>/players` - 比赛玩家数据
- `GET /api/leaderboard` - 排行榜数据

### 自定义比赛接口
- `GET /api/custom-tournaments` - 自定义比赛列表
- `POST /api/custom-tournaments` - 创建自定义比赛
- `GET /api/custom-tournaments/<id>` - 比赛详情
- `POST /api/custom-tournaments/<id>/matches` - 关联比赛

## 配置文件

### config.json
包含抓取器配置、API设置、调度时间等：
- 抓取时间配置（默认：08:00, 14:00, 20:00）
- API请求参数
- 数据存储路径配置

### nginx.conf
Nginx配置文件，用于前端部署。

## 注意事项

1. **时区设置**: 系统使用 Asia/Shanghai 时区
2. **数据抓取频率**: 默认每日6:00, 22:00, 22:30, 23:00, 23:30, 00:00执行抓取
3. **日志文件**: 所有日志存储在 `logs/` 目录
4. **数据备份**: 支持自动数据备份，保留7天
5. **端口**: API服务器默认运行在 5001 端口

## 故障排除

### 常见问题
- 调度器启动失败: 检查Python环境和依赖包
- API服务无法启动: 检查数据库连接配置
- 数据抓取失败: 检查网络连接和API配置

### 日志查看
```bash
# 查看调度器日志
tail -f logs/scheduler_$(date +%Y%m%d).log

# 查看API服务日志
tail -f logs/csgo_api.log
```