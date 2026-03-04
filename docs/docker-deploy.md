# Thinking Platform — Docker 部署指南

## 目录

- [架构总览](#架构总览)
- [前置条件](#前置条件)
- [文件结构](#文件结构)
- [部署顺序详解](#部署顺序详解)
- [一键部署](#一键部署)
- [手动分步部署](#手动分步部署)
- [更新发布](#更新发布)
- [运维命令](#运维命令)
- [故障排查](#故障排查)
- [高可用说明](#高可用说明)

---

## 架构总览

```
                         用户浏览器
                             │
                             ▼
                    ┌─────────────────┐
                    │   Nginx (:80)   │  ← 网关 + 负载均衡
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   /api/auth/*        /api/experiment/*    /api/modules/*
   /api/auth/*        /api/experiment/*    /api/modules/*
          │                  │                  │
          ▼                  ▼                  ▼
  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
  │ Python 主节点  │  │ Python 主节点  │  │  Java 主节点   │
  │   (:8001)     │  │   (:8001)     │  │   (:8002)     │
  ├───────────────┤  ├───────────────┤  ├───────────────┤
  │ Python 备节点  │  │ Python 备节点  │  │  Java 备节点   │
  │   (:8011)     │  │   (:8011)     │  │   (:8012)     │
  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  PostgreSQL     │
                    │  (:2345)        │
                    └─────────────────┘

  Frontend: Vue 3 静态文件由独立 Nginx 容器提供
  网关 Nginx 将 / 路径反向代理到 Frontend 容器
```

### 服务清单

| 服务 | 容器名 | 端口 | 技术栈 | 职责 |
|------|--------|------|--------|------|
| db-init | db-init | — | Python script | 初始化数据库（运行后退出） |
| auth-python | auth-python | 8001 | FastAPI | 认证 + 实验模块 API |
| auth-python-backup | auth-python-backup | 8011 | FastAPI | 认证备用节点 |
| module-java | module-java | 8002 | Spring Boot | 模块管理 + 权限 API |
| module-java-backup | module-java-backup | 8012 | Spring Boot | 模块管理备用节点 |
| frontend | frontend | 80(内部) | Vue 3 + Nginx | 前端静态文件 |
| nginx | nginx | 80 | Nginx | 网关 / 反向代理 / 负载均衡 |

---

## 前置条件

### 服务器要求
- **OS**: Linux (Ubuntu 20.04+ / CentOS 7+ / Debian 10+)
- **内存**: ≥ 4GB
- **磁盘**: ≥ 10GB 可用空间
- **网络**: 可访问 PostgreSQL 数据库 (`111.231.145.50:2345`)

### 软件要求
- **Docker**: ≥ 20.10 ([安装指南](https://docs.docker.com/engine/install/))
- **Docker Compose**: ≥ 2.0 (Docker Desktop 自带, 或 `docker compose` 插件)
- **Git**: 用于拉取代码

```bash
# 验证 Docker 版本
docker --version        # Docker version 24.x+
docker compose version  # Docker Compose version v2.x+
```

---

## 文件结构

```
thinking/
├── deploy.sh                 ← 一键部署脚本
├── docker-compose.yml        ← Docker Compose 编排
├── .env.example              ← 环境变量模板
├── .env                      ← 实际环境变量（不入库）
│
├── backend-python/           ← Python 服务
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── main.py               ← 入口（含 auth + experiment 路由）
│   ├── auth.py
│   ├── experiment.py
│   ├── database.py
│   └── config.py
│
├── backend-java/             ← Java 服务
│   ├── Dockerfile            ← 多阶段构建（Maven build → JRE runtime）
│   ├── .dockerignore
│   ├── pom.xml
│   └── src/
│
├── frontend/                 ← Vue 3 前端
│   ├── Dockerfile            ← 多阶段构建（npm build → Nginx serve）
│   ├── .dockerignore
│   ├── nginx.conf            ← 前端容器的 Nginx 配置（SPA fallback）
│   ├── package.json
│   └── src/
│
├── nginx/                    ← 网关 Nginx
│   └── nginx.conf            ← 反向代理 + 负载均衡配置
│
└── sql/                      ← 数据库初始化脚本
    ├── init.sql              ← 基础表（users, modules, permissions）
    └── experiment.sql        ← 实验表（experiments, plates, wells）
```

---

## 部署顺序详解

> **核心原则**: 按依赖链从底向上启动，确保下游服务就绪后再启动上游。

### 🔄 完整启动顺序

```
Step 0: 配置环境变量 (.env)
    │
    ▼
Step 1: 数据库初始化 (db-init)
    │   创建 database + 表结构 + 初始数据
    │   运行完毕后自动退出
    ▼
Step 2: 构建 Docker 镜像
    │   并行构建: Python / Java / Frontend
    │   ├── backend-python: pip install → 复制代码
    │   ├── backend-java:   Maven build → 复制 JAR
    │   └── frontend:       npm build → 复制 dist 到 Nginx
    ▼
Step 3: 启动后端服务
    │   ├── auth-python        (主) → :8001
    │   ├── auth-python-backup (备) → :8011
    │   ├── module-java        (主) → :8002
    │   └── module-java-backup (备) → :8012
    │   等待 healthcheck 通过...
    ▼
Step 4: 启动前端容器
    │   frontend → 内部 :80 提供静态文件
    ▼
Step 5: 启动 Nginx 网关
        nginx → :80 (对外)
        ├── /api/auth/*       → python_service (主/备)
        ├── /api/experiment/* → python_service (主/备)
        ├── /api/modules/*    → java_service (主/备)
        └── /*                → frontend (静态文件)
```

### 为什么是这个顺序？

| 顺序 | 原因 |
|------|------|
| DB init 最先 | 后端服务启动时会连接数据库，表必须已存在 |
| 镜像构建在启动前 | 确保所有代码已编译打包，避免运行时失败 |
| 后端先于前端 | 前端 `depends_on` 后端，确保 API 可用 |
| Nginx 最后 | Nginx 依赖所有 upstream 已启动，否则 502 |

---

## 一键部署

### 首次部署

```bash
# 1. 克隆代码
git clone https://github.com/linliuan-stack/thinking.git
cd thinking

# 2. 创建配置文件
cp .env.example .env
# 编辑 .env，确认数据库连接信息

# 3. 一键部署
./deploy.sh start
```

### 脚本命令一览

| 命令 | 说明 |
|------|------|
| `./deploy.sh start` | 首次部署 / 全量重建 |
| `./deploy.sh update` | 代码更新后增量部署 |
| `./deploy.sh stop` | 停止所有服务 |
| `./deploy.sh status` | 查看状态 + 健康检查 |
| `./deploy.sh logs` | 查看实时日志 |
| `./deploy.sh restart` | 重启所有服务 |

---

## 手动分步部署

如果你需要更精细的控制，可以按以下步骤手动执行：

### Step 0: 准备环境变量

```bash
cp .env.example .env
vim .env
```

`.env` 文件内容:

```env
DB_HOST=111.231.145.50
DB_PORT=2345
DB_NAME=thinking
DB_USER=postgres
DB_PASSWORD=tech-coffee
SECRET_KEY=your-production-secret-key
NGINX_PORT=80
```

### Step 1: 初始化数据库

```bash
docker compose up db-init
# 看到 "DB init done" 表示成功
# 此容器运行后自动退出
```

### Step 2: 构建镜像

```bash
# 并行构建所有服务（首次约 3-5 分钟）
docker compose build --parallel

# 或单独构建某个服务
docker compose build auth-python
docker compose build module-java
docker compose build frontend
```

### Step 3: 启动后端

```bash
# 启动 Python 服务（主 + 备）
docker compose up -d auth-python auth-python-backup

# 启动 Java 服务（主 + 备）
docker compose up -d module-java module-java-backup

# 验证后端健康
curl http://localhost:8001/api/auth/health
# → {"status":"ok","service":"auth-python"}

curl http://localhost:8002/api/modules/health
# → {"service":"module-java","status":"ok"}
```

### Step 4: 启动前端

```bash
docker compose up -d frontend
```

### Step 5: 启动 Nginx 网关

```bash
docker compose up -d nginx

# 验证整体访问
curl http://localhost
# → 返回 HTML 页面
```

### 一次性全部启动（简化版）

```bash
docker compose up -d
# Docker Compose 会根据 depends_on 自动处理启动顺序
```

---

## 更新发布

### 场景 1: 只改了 Python 代码

```bash
# 重建并重启 Python 服务（零停机: 备节点继续服务）
docker compose build auth-python
docker compose up -d --no-deps auth-python
# 等待主节点健康后，再更新备节点
docker compose build auth-python-backup
docker compose up -d --no-deps auth-python-backup
```

### 场景 2: 只改了 Java 代码

```bash
docker compose build module-java
docker compose up -d --no-deps module-java
docker compose build module-java-backup
docker compose up -d --no-deps module-java-backup
```

### 场景 3: 只改了前端代码

```bash
docker compose build frontend
docker compose up -d --no-deps frontend
# Nginx 不需要重启，自动代理到新的前端容器
```

### 场景 4: 改了 Nginx 配置

```bash
# 方式 1: 热重载（不中断服务）
docker compose exec nginx nginx -s reload

# 方式 2: 重启容器
docker compose restart nginx
```

### 场景 5: 全量更新（推荐用脚本）

```bash
git pull
./deploy.sh update
```

### 场景 6: 数据库 Schema 变更

```bash
# 重新运行 db-init（SQL 使用 IF NOT EXISTS，安全重复执行）
docker compose up db-init
```

---

## 运维命令

### 查看日志

```bash
# 所有服务日志
docker compose logs -f

# 某个服务的日志
docker compose logs -f auth-python
docker compose logs -f module-java
docker compose logs -f nginx

# 最近 100 行
docker compose logs --tail=100 auth-python
```

### 查看状态

```bash
docker compose ps

# 输出示例:
# NAME                 STATUS          PORTS
# auth-python          Up (healthy)    0.0.0.0:8001→8001/tcp
# auth-python-backup   Up              0.0.0.0:8011→8001/tcp
# module-java          Up (healthy)    0.0.0.0:8002→8002/tcp
# module-java-backup   Up              0.0.0.0:8012→8002/tcp
# frontend             Up              80/tcp
# nginx                Up              0.0.0.0:80→80/tcp
```

### 进入容器调试

```bash
docker compose exec auth-python bash
docker compose exec module-java bash
docker compose exec nginx sh
```

### 资源占用

```bash
docker stats --no-stream
```

### 清理

```bash
# 停止并删除容器
docker compose down

# 停止并删除容器 + 镜像
docker compose down --rmi local

# 清理所有未使用的镜像
docker image prune -a
```

---

## 故障排查

### 常见问题

#### 1. 端口被占用

```bash
# 检查 80 端口
sudo lsof -i :80
# 修改 .env 中的 NGINX_PORT=8080
```

#### 2. 数据库连接失败

```bash
# 从 Docker 容器内测试连接
docker compose exec auth-python python -c "
from database import get_connection
conn = get_connection()
print('Connected!')
conn.close()
"
```

#### 3. Java 构建 OOM

```bash
# 在 docker-compose.yml 的 module-java 下添加:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

#### 4. 前端 API 404

```bash
# 检查 Nginx 配置是否正确挂载
docker compose exec nginx cat /etc/nginx/nginx.conf
# 检查 upstream 是否可达
docker compose exec nginx ping auth-python
```

#### 5. 健康检查失败

```bash
# 查看某个服务的详细状态
docker inspect $(docker compose ps -q auth-python) | grep -A 10 Health
```

---

## 高可用说明

### 当前 HA 架构

```
Nginx (least_conn 负载均衡)
├── Python 主节点 (:8001)   ← 正常流量
├── Python 备节点 (:8011)   ← 主节点故障时自动切换
├── Java   主节点 (:8002)   ← 正常流量
└── Java   备节点 (:8012)   ← 主节点故障时自动切换
```

### 故障转移机制

- Nginx 使用 `least_conn` 最少连接策略分发流量
- 备节点标记为 `backup`，仅在主节点不可用时激活
- `proxy_next_upstream error timeout http_502 http_503` — 主节点返回 502/503 时自动重试备节点
- 每个后端容器都有 `HEALTHCHECK`，Docker 自动监控并重启不健康的容器
- `restart: unless-stopped` 确保容器崩溃后自动重启

### 滚动更新（零停机）

更新主节点时备节点自动接管，步骤:

```bash
# 1. 先更新备节点（此时主节点正常服务）
docker compose up -d --no-deps auth-python-backup
# 2. 等备节点就绪
sleep 10
# 3. 更新主节点（此时备节点接管流量）
docker compose up -d --no-deps auth-python
# 4. 等主节点就绪，流量自动回到主节点
```

---

## 快速参考卡

```
┌────────────────────────────────────────────────┐
│              部署快速参考                        │
├────────────────────────────────────────────────┤
│                                                │
│  首次部署:     ./deploy.sh start               │
│  代码更新:     ./deploy.sh update              │
│  查看状态:     ./deploy.sh status              │
│  查看日志:     ./deploy.sh logs                │
│  停止服务:     ./deploy.sh stop                │
│  重启服务:     ./deploy.sh restart             │
│                                                │
│  单服务重建:   docker compose build <service>  │
│  单服务重启:   docker compose restart <service>│
│  进入容器:     docker compose exec <svc> bash  │
│                                                │
│  健康检查:                                      │
│    Python:  curl localhost:8001/api/auth/health │
│    Java:    curl localhost:8002/api/modules/health │
│    前端:    curl localhost                      │
│                                                │
└────────────────────────────────────────────────┘
```
