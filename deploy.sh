#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  Thinking Platform — 一键部署脚本
#  用法: ./deploy.sh [命令]
#
#  命令:
#    start    首次部署 / 全量重建 (默认)
#    update   代码更新后重新部署
#    stop     停止所有服务
#    status   查看服务状态
#    logs     查看日志
#    restart  重启所有服务
# ============================================================

COMPOSE="docker compose"
command -v docker compose &>/dev/null || COMPOSE="docker-compose"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }
step() { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }

CMD="${1:-start}"

check_env() {
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            warn ".env 不存在，已从 .env.example 复制，请检查配置后重新运行"
            exit 1
        else
            err ".env 文件不存在，请参考 .env.example 创建"
            exit 1
        fi
    fi
    log ".env 配置文件已就绪"
}

case "$CMD" in

  start)
    step "Step 0/5: 检查环境"
    check_env

    step "Step 1/5: 初始化数据库"
    $COMPOSE up db-init
    log "数据库初始化完成"

    step "Step 2/5: 构建 Docker 镜像"
    $COMPOSE build --parallel auth-python module-java frontend
    log "所有镜像构建完成"

    step "Step 3/5: 启动后端服务 (Python + Java)"
    $COMPOSE up -d auth-python auth-python-backup module-java module-java-backup
    log "后端服务已启动"

    step "Step 4/5: 等待后端就绪..."
    sleep 5
    for svc in auth-python module-java; do
        if $COMPOSE ps "$svc" | grep -q "Up\|running"; then
            log "$svc 已就绪"
        else
            warn "$svc 可能尚未就绪，请检查日志: $COMPOSE logs $svc"
        fi
    done

    step "Step 5/5: 启动前端 + Nginx 网关"
    $COMPOSE up -d frontend nginx
    log "前端和 Nginx 已启动"

    echo ""
    step "部署完成!"
    echo ""
    log "访问地址:  http://localhost:$(grep NGINX_PORT .env 2>/dev/null | cut -d= -f2 || echo 80)"
    echo ""
    log "服务状态:"
    $COMPOSE ps
    ;;

  update)
    step "代码更新部署"
    check_env

    step "Step 1/3: 重新构建变更的镜像"
    $COMPOSE build --parallel auth-python module-java frontend
    log "镜像构建完成"

    step "Step 2/3: 滚动更新后端"
    $COMPOSE up -d --no-deps auth-python auth-python-backup
    $COMPOSE up -d --no-deps module-java module-java-backup
    log "后端已更新"

    step "Step 3/3: 更新前端 + 重载 Nginx"
    $COMPOSE up -d --no-deps frontend
    $COMPOSE exec nginx nginx -s reload 2>/dev/null || $COMPOSE restart nginx
    log "前端已更新，Nginx 已重载"

    echo ""
    step "更新完成!"
    $COMPOSE ps
    ;;

  stop)
    step "停止所有服务"
    $COMPOSE down
    log "所有服务已停止"
    ;;

  status)
    $COMPOSE ps
    echo ""
    echo "健康检查:"
    for url in "http://localhost:8001/api/auth/health" "http://localhost:8002/api/modules/health"; do
        resp=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [ "$resp" = "200" ]; then
            log "$url → 200 OK"
        else
            err "$url → $resp"
        fi
    done
    ;;

  logs)
    $COMPOSE logs -f --tail=50
    ;;

  restart)
    step "重启所有服务"
    $COMPOSE restart
    log "所有服务已重启"
    $COMPOSE ps
    ;;

  *)
    echo "用法: $0 {start|update|stop|status|logs|restart}"
    exit 1
    ;;
esac
