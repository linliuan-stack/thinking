# Thinking Platform — Docker 部署指南

## 目录

- [架构总览](#架构总览)
- [前置条件](#前置条件)
- [文件结构](#文件结构)
- [部署顺序详解](#部署顺序详解)
- [一键部署](#一键部署)
- [前端 Docker 发布详解](#前端-docker-发布详解)
- [后端 Docker 发布详解](#后端-docker-发布详解)
- [推送镜像到仓库](#推送镜像到仓库)
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
     /api/auth/*      /api/experiment/*    /api/modules/*
          │                  │                  │
          ▼                  ▼                  ▼
  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
  │ Python 主节点  │  │ Python 主节点  │  │  Java 主节点   │
  │   (:8001)     │  │   (:8001)     │  │   (:8002)     │
  ├───────────────┤  ├───────────────┤  ├───────────────┤
  │ Python 备节点  │  │ Python 备节点  │  │  Java 备节点   │
  │   (:8011)     │  │   (:8011)     │  │   (:8012)     │
  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
          └──────────────────┼──────────────────┘
                    ┌────────▼────────┐
                    │  PostgreSQL     │
                    │  (:2345)        │
                    └─────────────────┘
```

```
  前端容器内部:
  ┌──────────────────────────────────────────────┐
  │  Frontend Container (thinking-frontend)      │
  │  ┌────────────────────────────────────────┐  │
  │  │  Nginx (内部 :80)                      │  │
  │  │  ├── /index.html       → Vue SPA      │  │
  │  │  ├── /assets/*.js,css  → 静态资源      │  │
  │  │  └── 其他路径           → /index.html  │  │
  │  └────────────────────────────────────────┘  │
  └──────────────────────────────────────────────┘
                    ▲
                    │ proxy_pass
           Nginx 网关 (location /)
```

### 服务清单

| 服务 | 镜像名 | 端口 | 技术栈 | 职责 |
|------|--------|------|--------|------|
| db-init | python:3.12-slim | — | Python script | 初始化数据库（运行后退出） |
| auth-python | thinking-python | 8001 | FastAPI | 认证 + 实验模块 API |
| auth-python-backup | thinking-python | 8011 | FastAPI | 认证备用节点 |
| module-java | thinking-java | 8002 | Spring Boot | 模块管理 + 权限 API |
| module-java-backup | thinking-java | 8012 | Spring Boot | 模块管理备用节点 |
| **frontend** | **thinking-frontend** | **80(内部)** | **Vue 3 + Nginx** | **前端静态文件** |
| nginx | nginx:alpine | 80 | Nginx | 网关 / 反向代理 / 负载均衡 |

---

## 前置条件

### 软件要求
- **Docker**: ≥ 20.10
- **Docker Compose**: ≥ 2.0
- **Git**: 用于拉取代码

```bash
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
├── frontend/                 ← Vue 3 前端
│   ├── Dockerfile            ← ⭐ 多阶段构建（npm build → Nginx serve）
│   ├── .dockerignore         ← 排除 node_modules/dist 加速构建
│   ├── nginx.conf            ← 前端容器 Nginx（SPA fallback + 缓存 + 安全头）
│   ├── package.json
│   └── src/
│
├── backend-python/           ← Python 服务
│   ├── Dockerfile
│   └── ...
│
├── backend-java/             ← Java 服务
│   ├── Dockerfile            ← 多阶段构建（Maven build → JRE runtime）
│   └── ...
│
├── nginx/                    ← 网关 Nginx
│   └── nginx.conf
│
└── sql/                      ← 数据库初始化脚本
    ├── init.sql
    └── experiment.sql
```

---

## 部署顺序详解

> **核心原则**: 按依赖链从底向上启动，确保下游服务就绪后再启动上游。

```
Step 0: 配置环境变量 (.env)
    ▼
Step 1: 数据库初始化 (db-init)  ← 创建 database + 表结构
    ▼
Step 2: 构建 Docker 镜像        ← 并行构建 Python / Java / Frontend
    ▼
Step 3: 启动后端服务             ← Python(:8001,:8011) + Java(:8002,:8012)
    ▼
Step 4: 启动前端容器             ← Frontend(内部:80, 提供静态文件)
    ▼
Step 5: 启动 Nginx 网关          ← 反向代理到所有上游
```

| 顺序 | 原因 |
|------|------|
| DB init 最先 | 后端启动时会连接数据库，表必须已存在 |
| 镜像构建在启动前 | 确保所有代码已编译打包 |
| 后端先于前端 | 前端 `depends_on` 后端 |
| 前端先于 Nginx | Nginx upstream 依赖前端容器 |
| Nginx 最后 | 依赖所有 upstream 已启动 |

---

## 一键部署

```bash
git clone https://github.com/linliuan-stack/thinking.git
cd thinking
cp .env.example .env          # 编辑 .env 确认配置
./deploy.sh start             # 一键部署
```

### 脚本命令一览

| 命令 | 说明 |
|------|------|
| `./deploy.sh start` | 首次部署 / 全量重建 |
| `./deploy.sh update` | 代码更新后增量部署 |
| `./deploy.sh build [服务名]` | 只构建镜像, 不启动 |
| `./deploy.sh push` | 构建并推送镜像到仓库 |
| `./deploy.sh stop` | 停止所有服务 |
| `./deploy.sh status` | 查看状态 + 健康检查 |
| `./deploy.sh logs [服务名]` | 查看日志 |
| `./deploy.sh restart` | 重启所有服务 |

---

## 前端 Docker 发布详解

### Dockerfile 逐层解析

```dockerfile
# ── Stage 1: 编译阶段 ──
FROM node:22-alpine AS build          # 使用 Alpine 版 Node 减小体积

ARG API_BASE_URL=""                   # 构建参数: API 地址
ENV VITE_API_BASE_URL=${API_BASE_URL} # 注入到 Vite 环境变量

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts           # 只安装依赖, 不运行脚本

COPY . .
RUN npm run build                     # vue-tsc 类型检查 + vite 生产构建
                                      # 输出到 /app/dist/

# ── Stage 2: 运行阶段 ──
FROM nginx:1.27-alpine                # 最终镜像只有 Nginx (~40MB)

COPY --from=build /app/dist /usr/share/nginx/html  # 复制构建产物
COPY nginx.conf /etc/nginx/conf.d/default.conf     # 自定义 Nginx 配置

EXPOSE 80
HEALTHCHECK CMD wget -qO- http://localhost/ > /dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

#### 为什么使用多阶段构建？

| | 单阶段 | 多阶段 (当前) |
|---|---|---|
| 镜像大小 | ~1.2 GB (含 Node + node_modules) | **~65 MB** (仅 Nginx + 静态文件) |
| 安全性 | 包含源代码和依赖 | **只有编译产物** |
| 启动速度 | 需要 Node 进程 | **Nginx 毫秒级启动** |

### 前端 nginx.conf 配置说明

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    # SPA 路由: 所有非文件请求回退到 index.html
    # 这样 /login, /experiment/1 等前端路由才能正确工作
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源长期缓存 (Vite 构建的文件名含 hash, 天然支持缓存)
    location ~* \.(js|css|png|jpg|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # index.html 不缓存, 确保每次获取最新版
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

### 开发 vs 生产 API 路由对比

| | 开发模式 (Vite dev server) | 生产模式 (Docker) |
|---|---|---|
| 前端运行方式 | `npx vite --port 3000` | Nginx 容器内提供静态文件 |
| API 路由 | Vite proxy (`vite.config.ts`) | Nginx 网关反向代理 |
| API 请求路径 | `/api/auth/*` → Vite → `localhost:8001` | `/api/auth/*` → Nginx → `auth-python:8001` |
| 热更新 | ✅ 有 | ❌ 无（需重新构建） |

### 前端独立构建

```bash
# === 方式 1: 使用 docker compose 构建 ===
docker compose build frontend

# === 方式 2: 独立构建（不依赖 docker-compose.yml）===
cd frontend
docker build -t thinking-frontend:latest .

# === 方式 3: 指定自定义 API 地址（前端独立部署到 CDN 时使用）===
cd frontend
docker build \
  --build-arg API_BASE_URL=https://api.example.com \
  -t thinking-frontend:latest .

# === 方式 4: 指定版本 Tag ===
docker build -t thinking-frontend:v1.2.0 .
docker build -t thinking-frontend:$(git rev-parse --short HEAD) .
```

### 前端独立运行

```bash
# 直接运行前端容器
docker run -d \
  --name thinking-frontend \
  -p 3000:80 \
  thinking-frontend:latest

# 验证
curl http://localhost:3000
# → 返回 Vue SPA 的 index.html

# 查看日志
docker logs thinking-frontend

# 停止
docker stop thinking-frontend && docker rm thinking-frontend
```

### 前端镜像更新流程

```
开发者修改前端代码 (src/*.vue, src/*.ts)
         │
         ▼
    git commit && git push
         │
         ▼
    ┌─────────────────────────┐
    │  docker compose build   │
    │  frontend               │
    │  (多阶段构建 ~30秒)      │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  docker compose up -d   │
    │  --no-deps frontend     │
    │  (替换容器 ~2秒)         │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  用户刷新浏览器即可看到   │
    │  最新版本                │
    └─────────────────────────┘
```

```bash
# 完整命令:
docker compose build frontend && docker compose up -d --no-deps frontend
# 或使用脚本:
./deploy.sh build frontend
```

### 前端构建常见问题

#### TypeScript 编译失败
```bash
# 查看完整构建日志
docker compose build --no-cache --progress=plain frontend 2>&1 | less
# 先在本地验证
cd frontend && npx vue-tsc --noEmit
```

#### 静态资源 404
```bash
# 进入容器检查文件
docker compose exec frontend ls -la /usr/share/nginx/html/
docker compose exec frontend ls -la /usr/share/nginx/html/assets/
```

#### API 请求跨域
```
# 推荐: 通过 Nginx 网关代理（同域, 无跨域问题）
# 独立部署: 需在后端配置 CORS 允许前端域名
```

---

## 后端 Docker 发布详解

### Python 服务

```bash
# 构建
docker compose build auth-python
# 或独立构建
cd backend-python && docker build -t thinking-python:latest .

# 独立运行
docker run -d --name thinking-python \
  -p 8001:8001 \
  -e DB_HOST=111.231.145.50 \
  -e DB_PORT=2345 \
  -e DB_NAME=thinking \
  -e DB_USER=postgres \
  -e DB_PASSWORD=tech-coffee \
  thinking-python:latest

# 验证
curl http://localhost:8001/api/auth/health
```

#### Python Dockerfile 结构

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl   # 用于 healthcheck
COPY requirements.txt . && pip install -r ...    # 安装依赖
COPY . .                                         # 复制代码
EXPOSE 8001
HEALTHCHECK CMD curl -f http://localhost:8001/api/auth/health
CMD ["python", "main.py"]
```

### Java 服务

```bash
# 构建 (多阶段: Maven 编译 → JRE 运行)
docker compose build module-java
# 或独立构建
cd backend-java && docker build -t thinking-java:latest .

# 独立运行
docker run -d --name thinking-java \
  -p 8002:8002 \
  -e SPRING_DATASOURCE_URL=jdbc:postgresql://111.231.145.50:2345/thinking \
  -e SPRING_DATASOURCE_USERNAME=postgres \
  -e SPRING_DATASOURCE_PASSWORD=tech-coffee \
  thinking-java:latest

# 验证
curl http://localhost:8002/api/modules/health
```

#### Java Dockerfile 结构

```dockerfile
# Stage 1: Maven 编译
FROM maven:3.9-eclipse-temurin-21 AS build
COPY pom.xml . && mvn dependency:resolve         # 缓存依赖
COPY src ./src && mvn package -DskipTests         # 编译 JAR

# Stage 2: JRE 运行
FROM eclipse-temurin:21-jre
COPY --from=build /build/target/*.jar app.jar     # 只复制 JAR
EXPOSE 8002
HEALTHCHECK CMD curl -f http://localhost:8002/api/modules/health
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 推送镜像到仓库

### 配置镜像仓库

在 `.env` 中设置:

```env
# Docker Hub
REGISTRY=docker.io/your-username

# 阿里云容器镜像服务
REGISTRY=registry.cn-hangzhou.aliyuncs.com/your-namespace

# GitHub Container Registry
REGISTRY=ghcr.io/your-org

# 私有仓库
REGISTRY=registry.example.com:5000

# 版本标签
TAG=v1.0.0
```

### 一键构建并推送

```bash
# 登录仓库
docker login registry.cn-hangzhou.aliyuncs.com   # 阿里云
docker login                                      # Docker Hub
docker login ghcr.io                              # GitHub

# 使用脚本一键推送全部
./deploy.sh push
```

脚本会自动:
1. 构建 `thinking-python`, `thinking-java`, `thinking-frontend` 三个镜像
2. 打上 `REGISTRY/IMAGE:TAG` 标签
3. 推送到配置的仓库

### 手动推送单个镜像

```bash
# 示例: 只推送前端
REGISTRY="registry.cn-hangzhou.aliyuncs.com/myns"
TAG="v1.2.0"

docker compose build frontend
docker tag thinking-frontend:latest ${REGISTRY}/thinking-frontend:${TAG}
docker push ${REGISTRY}/thinking-frontend:${TAG}
```

### 在目标服务器拉取并运行

```bash
# 在目标服务器上
export REGISTRY="registry.cn-hangzhou.aliyuncs.com/myns"
export TAG="v1.0.0"

docker pull ${REGISTRY}/thinking-frontend:${TAG}
docker pull ${REGISTRY}/thinking-python:${TAG}
docker pull ${REGISTRY}/thinking-java:${TAG}

# 使用 docker-compose.yml 启动
# .env 中设置好 REGISTRY 和 TAG, 然后:
docker compose up -d
```

---

## 手动分步部署

### Step 0: 准备环境变量

```bash
cp .env.example .env && vim .env
```

### Step 1: 初始化数据库

```bash
docker compose up db-init
```

### Step 2: 构建镜像

```bash
docker compose build --parallel                # 全部
docker compose build frontend                  # 仅前端
docker compose build auth-python module-java   # 仅后端
```

### Step 3: 启动后端

```bash
docker compose up -d auth-python auth-python-backup module-java module-java-backup
curl http://localhost:8001/api/auth/health      # 验证 Python
curl http://localhost:8002/api/modules/health   # 验证 Java
```

### Step 4: 启动前端

```bash
docker compose up -d frontend
```

### Step 5: 启动 Nginx 网关

```bash
docker compose up -d nginx
curl http://localhost                           # 验证首页
```

### 简化: 一次性全部启动

```bash
docker compose up -d
```

---

## 更新发布

### 场景 1: 只改了前端代码

```bash
docker compose build frontend
docker compose up -d --no-deps frontend
```

### 场景 2: 只改了 Python 代码

```bash
# 零停机: 备节点继续服务
docker compose build auth-python
docker compose up -d --no-deps auth-python
sleep 10
docker compose up -d --no-deps auth-python-backup
```

### 场景 3: 只改了 Java 代码

```bash
docker compose build module-java
docker compose up -d --no-deps module-java
sleep 10
docker compose up -d --no-deps module-java-backup
```

### 场景 4: 改了 Nginx 配置

```bash
docker compose exec nginx nginx -s reload       # 热重载
```

### 场景 5: 全量更新

```bash
git pull && ./deploy.sh update
```

### 场景 6: 数据库 Schema 变更

```bash
docker compose up db-init
```

---

## 运维命令

```bash
# 日志
docker compose logs -f                          # 全部
docker compose logs -f frontend                 # 仅前端
docker compose logs -f auth-python              # 仅 Python

# 状态
docker compose ps

# 进入容器
docker compose exec frontend sh                 # 前端 (Alpine, 用 sh)
docker compose exec auth-python bash             # Python
docker compose exec module-java bash             # Java
docker compose exec nginx sh                     # Nginx 网关

# 查看前端静态文件
docker compose exec frontend ls -la /usr/share/nginx/html/

# 资源占用
docker stats --no-stream

# 清理
docker compose down                             # 停止
docker compose down --rmi local                 # 停止 + 删除镜像
docker image prune -a                           # 清理无用镜像
```

---

## 故障排查

### 前端相关

```bash
# 前端构建失败 → 查看详细日志
docker compose build --no-cache --progress=plain frontend

# 前端 404 → 检查静态文件
docker compose exec frontend ls /usr/share/nginx/html/

# 前端路由刷新 404 → 检查 SPA fallback
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
# 确保有: try_files $uri $uri/ /index.html;

# API 请求失败 → 从前端容器内测试后端连通性
docker compose exec frontend wget -qO- http://auth-python:8001/api/auth/health
```

### 后端相关

```bash
# 数据库连接失败
docker compose exec auth-python python -c "
from database import get_connection
conn = get_connection(); print('OK'); conn.close()
"

# 健康检查失败
docker inspect $(docker compose ps -q auth-python) | grep -A 10 Health
```

### 端口冲突

```bash
sudo lsof -i :80       # 查看占用
# 修改 .env: NGINX_PORT=8080
```

---

## 高可用说明

```
Nginx (least_conn 负载均衡)
├── Python 主节点 (:8001)   ← 正常流量
├── Python 备节点 (:8011)   ← 主节点故障时自动切换
├── Java   主节点 (:8002)   ← 正常流量
└── Java   备节点 (:8012)   ← 主节点故障时自动切换
```

- **自动故障转移**: `proxy_next_upstream error timeout http_502 http_503`
- **自动重启**: `restart: unless-stopped` + Docker `HEALTHCHECK`
- **零停机更新**: 先更新备节点 → 等就绪 → 再更新主节点

---

## 快速参考卡

```
┌────────────────────────────────────────────────────────┐
│                    部署快速参考                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│  首次部署:       ./deploy.sh start                     │
│  代码更新:       ./deploy.sh update                    │
│  只构建镜像:     ./deploy.sh build [frontend|...]      │
│  推送到仓库:     ./deploy.sh push                      │
│  查看状态:       ./deploy.sh status                    │
│  查看日志:       ./deploy.sh logs [frontend|...]       │
│  停止服务:       ./deploy.sh stop                      │
│  重启服务:       ./deploy.sh restart                   │
│                                                        │
│  单独构建前端:   docker compose build frontend         │
│  单独更新前端:   docker compose up -d --no-deps frontend│
│  查看前端文件:   docker compose exec frontend ls /...  │
│                                                        │
│  健康检查:                                              │
│    Python:  curl localhost:8001/api/auth/health         │
│    Java:    curl localhost:8002/api/modules/health      │
│    前端:    curl localhost                              │
│                                                        │
│  镜像列表:   docker images | grep thinking-            │
│                                                        │
│  镜像大小参考:                                          │
│    thinking-frontend  ~65MB   (Nginx + 静态文件)       │
│    thinking-java      ~310MB  (JRE + JAR)              │
│    thinking-python    ~400MB  (Python + scipy)         │
│                                                        │
└────────────────────────────────────────────────────────┘
```
