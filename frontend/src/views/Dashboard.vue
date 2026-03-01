<template>
  <el-container class="dashboard-container">
    <el-header class="dashboard-header">
      <div class="header-left">
        <el-icon :size="28" color="#fff"><Monitor /></el-icon>
        <span class="brand">Thinking Platform</span>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" class="avatar">{{ userStore.user?.username?.charAt(0)?.toUpperCase() }}</el-avatar>
            <span class="username">{{ userStore.user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <el-tag :type="userStore.isAdmin ? 'danger' : 'info'" size="small">{{ userStore.user?.role }}</el-tag>
                {{ userStore.user?.username }}
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main class="dashboard-main">
      <div class="stats-row">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card stat-total">
              <div class="stat-content">
                <div class="stat-icon"><el-icon :size="40"><Grid /></el-icon></div>
                <div class="stat-info">
                  <div class="stat-number">{{ totalModules }}</div>
                  <div class="stat-label">全部模块</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card stat-accessible">
              <div class="stat-content">
                <div class="stat-icon"><el-icon :size="40"><CircleCheck /></el-icon></div>
                <div class="stat-info">
                  <div class="stat-number">{{ accessibleModules }}</div>
                  <div class="stat-label">可用模块</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card stat-python">
              <div class="stat-content">
                <div class="stat-icon"><el-icon :size="40"><Cpu /></el-icon></div>
                <div class="stat-info">
                  <div class="stat-number">{{ pythonModules }}</div>
                  <div class="stat-label">Python 服务</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card stat-java">
              <div class="stat-content">
                <div class="stat-icon"><el-icon :size="40"><Coffee /></el-icon></div>
                <div class="stat-info">
                  <div class="stat-number">{{ javaModules }}</div>
                  <div class="stat-label">Java 服务</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <el-card class="modules-card">
        <template #header>
          <div class="card-header">
            <span class="card-title"><el-icon><Menu /></el-icon> 模块列表</span>
            <el-tag type="info">共 {{ totalModules }} 个模块</el-tag>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="6" v-for="perm in permissions" :key="perm.module_id">
            <el-card
              :class="['module-card', { 'module-disabled': !perm.can_access }]"
              shadow="hover"
            >
              <div class="module-icon">
                <el-icon :size="36" :color="perm.can_access ? getIconColor(perm.service_type) : '#c0c4cc'">
                  <component :is="getIcon(perm.module_icon)" />
                </el-icon>
              </div>
              <h3 class="module-name">{{ perm.module_name }}</h3>
              <p class="module-desc">{{ perm.module_description }}</p>
              <div class="module-footer">
                <el-tag :type="perm.service_type === 'python' ? 'success' : 'warning'" size="small">
                  {{ perm.service_type }}
                </el-tag>
                <el-tag :type="perm.can_access ? 'success' : 'danger'" size="small" effect="plain">
                  {{ perm.can_access ? '可用' : '无权限' }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { moduleApi } from '../api'

const router = useRouter()
const userStore = useUserStore()

interface Permission {
  id: number
  user_id: number
  module_id: number
  can_access: boolean
  module_name: string
  module_description: string
  module_icon: string
  module_status: string
  service_type: string
}

const permissions = ref<Permission[]>([])

const totalModules = computed(() => permissions.value.length)
const accessibleModules = computed(() => permissions.value.filter(p => p.can_access).length)
const pythonModules = computed(() => permissions.value.filter(p => p.service_type === 'python').length)
const javaModules = computed(() => permissions.value.filter(p => p.service_type === 'java').length)

function getIconColor(serviceType: string) {
  return serviceType === 'python' ? '#67c23a' : '#e6a23c'
}

function getIcon(iconName: string) {
  const iconMap: Record<string, string> = {
    UserOutlined: 'User',
    BarChartOutlined: 'DataAnalysis',
    ShoppingCartOutlined: 'ShoppingCart',
    DatabaseOutlined: 'Coin',
    FileTextOutlined: 'Document',
    DashboardOutlined: 'Odometer',
    BellOutlined: 'Bell',
    ApiOutlined: 'Connection',
  }
  return iconMap[iconName] || 'Grid'
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(async () => {
  if (!userStore.user) return
  try {
    const res = await moduleApi.getPermissions(userStore.user.id)
    permissions.value = res.data
  } catch (e) {
    ElMessage.error('加载模块信息失败')
  }
})
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  background: #f0f2f5;
}

.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
}

.avatar {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
  font-weight: 600;
}

.username {
  font-size: 14px;
}

.dashboard-main {
  padding: 24px;
  overflow-y: auto;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  border: none;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-total .stat-icon { color: #409eff; }
.stat-accessible .stat-icon { color: #67c23a; }
.stat-python .stat-icon { color: #306998; }
.stat-java .stat-icon { color: #e6a23c; }

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.modules-card {
  border-radius: 12px;
  border: none;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-card {
  margin-bottom: 20px;
  border-radius: 12px;
  text-align: center;
  padding: 8px 0;
  transition: transform 0.2s;
  cursor: pointer;
}

.module-card:hover {
  transform: translateY(-4px);
}

.module-disabled {
  opacity: 0.5;
}

.module-icon {
  margin-bottom: 12px;
}

.module-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.module-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  min-height: 36px;
}

.module-footer {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>
