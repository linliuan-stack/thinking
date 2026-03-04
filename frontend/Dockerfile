# ==============================================================
#  Thinking Platform — Frontend Docker Image
#  多阶段构建: Node 编译 → Nginx 提供静态文件
#
#  构建:
#    docker build -t thinking-frontend .
#    docker build --build-arg API_BASE_URL=https://api.example.com -t thinking-frontend .
#
#  运行:
#    docker run -d -p 3000:80 thinking-frontend
# ==============================================================

# ---- Stage 1: 安装依赖 + 编译 ----
FROM node:22-alpine AS build

# 构建参数: 可在 docker build 时通过 --build-arg 覆盖 API 地址
# 默认为空字符串, 表示使用相对路径（通过同域 Nginx 网关代理）
ARG API_BASE_URL=""
ENV VITE_API_BASE_URL=${API_BASE_URL}

WORKDIR /app

# 先复制依赖声明文件, 利用 Docker 缓存层加速后续构建
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# 复制源代码并构建生产包
COPY . .
RUN npm run build

# ---- Stage 2: Nginx 提供静态文件 ----
FROM nginx:1.27-alpine

# 复制构建产物到 Nginx 默认目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制前端专用 Nginx 配置（SPA fallback + 缓存策略）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
