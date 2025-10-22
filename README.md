# 大畜之家 CS2 数据分析平台

一个基于5E对战平台的CS2比赛数据采集、分析和可视化系统，提供全面的玩家数据分析、比赛统计和排行榜功能。

## 🎯 项目概述

本项目是一个完整的CS2数据分析解决方案，包含：
- **数据采集系统**：自动从5E对战平台获取比赛数据
- **后端API服务**：提供RESTful API接口
- **前端可视化界面**：基于React + Ant Design的现代化Web界面
- **数据库存储**：MySQL数据库存储结构化数据
- **定时任务调度**：自动化数据更新机制

## ✨ 主要功能

### 📊 数据采集与存储
- 自动获取5E对战平台比赛数据
- 增量数据更新，避免重复采集
- 完整的比赛详情和玩家统计数据
- 支持VIP Plus数据获取
- 定时任务自动化运行

### 🎮 比赛分析
- 比赛列表查看和筛选
- 详细的比赛统计信息
- 地图数据分析
- 队伍表现对比
- 比赛回放Demo链接

### 👤 玩家分析
- 玩家搜索和详情查看
- 个人历史战绩统计
- 地图表现分析
- 最近比赛记录
- 多维度数据对比

### 🏆 排行榜系统
- 多种统计维度排行
- KD比、爆头率、ADR等指标
- 可自定义筛选条件
- 实时数据更新

### 🎪 自定义比赛
- 创建自定义比赛/锦标赛
- 队伍管理和统计
- 比赛关联和数据分析
- 锦标赛排行榜

## 🛠 技术栈

### 后端技术
- **Python 3.x** - 主要开发语言
- **Flask** - Web框架和API服务
- **MySQL** - 数据库存储
- **mysql-connector-python** - 数据库连接
- **Requests** - HTTP请求处理
- **Schedule** - 定时任务调度
- **Selenium** - Web自动化（如需要）

### 前端技术
- **React 19** - 前端框架
- **TypeScript** - 类型安全
- **Ant Design** - UI组件库
- **React Router** - 路由管理
- **Axios** - HTTP客户端
- **Day.js** - 日期处理

### 基础设施
- **Nginx** - 反向代理和静态文件服务
- **Docker** - 容器化部署（可选）
- **Shell Scripts** - 自动化脚本

## 📁 项目结构

```
dczj-cs2-analysis/
├── api_server.py              # Flask API服务器
├── config.json               # 系统配置文件
├── requirements.txt          # Python依赖
├── database_schema_optimized.sql  # 数据库表结构
├── fetch_match_details_optimized.py  # 比赛详情获取
├── fetch_match_ids.py        # 比赛ID获取
├── incremental_fetch.py      # 增量数据获取
├── scheduler.py              # 定时任务调度器
├── mysql_connector.py        # 数据库连接工具
├── csgo-dashboard/           # React前端应用
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── services/         # API服务
│   │   └── App.tsx          # 主应用组件
│   ├── package.json         # 前端依赖
│   └── public/              # 静态资源
├── data/                    # 数据存储目录
├── logs/                    # 日志文件
├── nginx.conf              # Nginx配置
├── *.sh                    # 各种启动脚本
└── README.md               # 项目文档
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Nginx（生产环境）

### 1. 克隆项目
```bash
git clone <repository-url>
cd dczj-cs2-analysis
```

### 2. 后端设置

#### 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 配置数据库
```bash
# 创建数据库
mysql -u root -p < database_schema_optimized.sql
```

#### 配置环境变量
创建 `.env` 文件：
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cs_match_data
```

#### 启动API服务
```bash
python api_server.py
```
API服务将在 `http://localhost:5001` 启动

### 3. 前端设置

#### 安装依赖
```bash
cd csgo-dashboard
npm install
```

#### 启动开发服务器
```bash
npm start
```
前端应用将在 `http://localhost:3000` 启动

### 4. 数据采集

#### 手动获取数据
```bash
# 获取比赛ID列表
python fetch_match_ids.py

# 获取比赛详情
python fetch_match_details_optimized.py

# 增量更新
python incremental_fetch.py
```

#### 启动定时任务
```bash
# 启动调度器
./start_scheduler.sh

# 停止调度器
./stop_scheduler.sh
```

## ⚙️ 配置说明

### config.json 配置项
```json
{
  "scheduler": {
    "fetch_times": ["08:00", "14:00", "20:00"],  // 定时获取时间
    "timezone": "Asia/Shanghai",                  // 时区设置
    "max_retries": 3,                            // 最大重试次数
    "retry_delay_minutes": 30                    // 重试延迟
  },
  "fetcher": {
    "request_timeout": 30,                       // 请求超时时间
    "request_delay": 0.5,                       // 请求间隔
    "max_pages_per_fetch": 50,                  // 每次获取最大页数
    "max_known_match_ids": 10000                // 最大已知比赛ID数
  },
  "api": {
    "base_url": "https://gate.5eplay.com/...",  // 5E API地址
    "uuid": "your-uuid",                        // API UUID
    "limit": 30,                                // 每页数据量
    "game_mode": "39"                           // 游戏模式
  }
}
```

## 🔧 API接口

### 主要API端点

#### 比赛相关
- `GET /api/matches` - 获取比赛列表
- `GET /api/match/<match_id>/players` - 获取比赛玩家数据
- `GET /api/maps` - 获取地图列表

#### 玩家相关
- `GET /api/players` - 获取玩家列表
- `GET /api/players/search` - 搜索玩家
- `GET /api/player/<steam_id>` - 获取玩家详情
- `GET /api/player/<steam_id>/stats` - 获取玩家统计
- `GET /api/player/<steam_id>/recent-matches` - 获取最近比赛

#### 排行榜
- `GET /api/leaderboard` - 获取排行榜数据
- `GET /api/leaderboard/stats-types` - 获取统计类型
- `GET /api/leaderboard/filters` - 获取筛选选项

#### 自定义比赛
- `GET /api/custom-tournaments` - 获取自定义比赛列表
- `POST /api/custom-tournaments` - 创建自定义比赛
- `PUT /api/custom-tournaments/<id>` - 更新比赛信息
- `DELETE /api/custom-tournaments/<id>` - 删除比赛

## 📊 数据库设计

### 主要数据表
- `matches` - 比赛基本信息
- `players` - 玩家基本信息
- `player_match_stats` - 玩家比赛统计
- `vip_plus_stats` - VIP Plus详细统计
- `custom_tournaments` - 自定义比赛
- `tournament_teams` - 比赛队伍
- `tournament_match_links` - 比赛关联

## 🔄 部署指南

### 生产环境部署

#### 1. 构建前端
```bash
cd csgo-dashboard
npm run build
```

#### 2. 配置Nginx
```bash
# 复制nginx配置
cp nginx.conf /etc/nginx/sites-available/csgo-dashboard
ln -s /etc/nginx/sites-available/csgo-dashboard /etc/nginx/sites-enabled/

# 重启Nginx
sudo systemctl restart nginx
```

#### 3. 启动服务
```bash
# 启动API服务
./csgo_api_service.sh

# 启动定时任务
./start_scheduler.sh
```

### Docker部署（可选）
```bash
# 构建镜像
docker build -t csgo-dashboard .

# 运行容器
docker run -d -p 80:80 -p 5001:5001 csgo-dashboard
```

## 📝 日志管理

### 日志文件位置
- `logs/fetch_YYYYMMDD.log` - 数据获取日志
- `logs/scheduler.log` - 调度器日志
- `logs/api_server.log` - API服务日志

### 日志级别
- INFO - 一般信息
- WARNING - 警告信息
- ERROR - 错误信息
- DEBUG - 调试信息

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 常见问题

### Q: 数据获取失败怎么办？
A: 检查网络连接和API配置，查看日志文件获取详细错误信息。

### Q: 前端页面无法访问？
A: 确保API服务正常运行，检查CORS配置和端口设置。

### Q: 数据库连接失败？
A: 检查数据库配置和网络连接，确保数据库服务正常运行。

### Q: 定时任务不执行？
A: 检查调度器日志，确认时区设置和任务配置正确。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issues
- 邮箱：[your-email@example.com]

---

**大畜之家 CS2 数据分析平台** - 让数据驱动你的游戏表现！