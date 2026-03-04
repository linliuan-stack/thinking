<template>
  <el-container class="page-container">
    <el-header class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push('/')" circle />
        <el-icon :size="28" color="#fff"><Monitor /></el-icon>
        <span class="brand">实验管理</span>
      </div>
      <div class="header-right">
        <span class="username" style="color:#fff">{{ userStore.user?.username }}</span>
      </div>
    </el-header>

    <el-main class="page-main">
      <el-card>
        <template #header>
          <div class="card-header">
            <span class="card-title"><el-icon><List /></el-icon> 实验列表</span>
            <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon> 新建实验</el-button>
          </div>
        </template>

        <el-table :data="experiments" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="实验名称" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="creator_name" label="创建人" width="100" />
          <el-table-column prop="plate_count" label="孔板数" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="$router.push(`/experiment/${row.id}`)">
                <el-icon><View /></el-icon> 进入
              </el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button type="danger" size="small"><el-icon><Delete /></el-icon></el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-main>

    <el-dialog v-model="showCreate" title="新建实验" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="实验名称">
          <el-input v-model="form.name" placeholder="输入实验名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="实验描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ArrowLeft, List, Plus, View, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { experimentApi } from '../../api'

const userStore = useUserStore()
const experiments = ref<any[]>([])
const showCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', description: '' })

async function loadExperiments() {
  const res = await experimentApi.listExperiments()
  experiments.value = res.data
}

async function handleCreate() {
  if (!form.value.name) return ElMessage.warning('请输入实验名称')
  creating.value = true
  try {
    await experimentApi.createExperiment(form.value.name, form.value.description)
    ElMessage.success('实验创建成功')
    showCreate.value = false
    form.value = { name: '', description: '' }
    await loadExperiments()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(id: number) {
  await experimentApi.deleteExperiment(id)
  ElMessage.success('已删除')
  await loadExperiments()
}

onMounted(loadExperiments)
</script>

<style scoped>
.page-container { height: 100vh; background: #f0f2f5; }
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; }
.brand { color: #fff; font-size: 20px; font-weight: 600; }
.page-main { padding: 24px; overflow-y: auto; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
</style>
