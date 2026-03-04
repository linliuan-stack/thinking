<template>
  <el-container class="page-container">
    <el-header class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push('/experiment')" circle />
        <el-icon :size="28" color="#fff"><Monitor /></el-icon>
        <span class="brand">{{ experiment?.name || '实验详情' }}</span>
      </div>
      <div class="header-right">
        <span class="username" style="color:#fff">{{ userStore.user?.username }}</span>
      </div>
    </el-header>

    <el-main class="page-main">
      <el-card style="margin-bottom: 20px">
        <template #header>
          <div class="card-header">
            <span class="card-title"><el-icon><Grid /></el-icon> 孔板列表</span>
            <el-button type="primary" @click="showCreatePlate = true"><el-icon><Plus /></el-icon> 新建孔板</el-button>
          </div>
        </template>
        <el-table :data="plates" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="孔板名称" />
          <el-table-column label="规格" width="100">
            <template #default="{ row }">{{ row.rows }} × {{ row.cols }}</template>
          </el-table-column>
          <el-table-column prop="filled_wells" label="已填孔位" width="100" />
          <el-table-column label="操作" width="320">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="$router.push(`/experiment/${experimentId}/plate/${row.id}`)">
                <el-icon><Edit /></el-icon> 编辑孔板
              </el-button>
              <el-button type="success" size="small" @click="$router.push(`/experiment/${experimentId}/plate/${row.id}/analysis`)">
                <el-icon><DataAnalysis /></el-icon> 数据分析
              </el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDeletePlate(row.id)">
                <template #reference>
                  <el-button type="danger" size="small"><el-icon><Delete /></el-icon></el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-main>

    <el-dialog v-model="showCreatePlate" title="新建孔板" width="450px">
      <el-form :model="plateForm" label-width="80px">
        <el-form-item label="孔板名称">
          <el-input v-model="plateForm.name" placeholder="如: Plate-001" />
        </el-form-item>
        <el-form-item label="行数">
          <el-input-number v-model="plateForm.rows" :min="1" :max="16" />
        </el-form-item>
        <el-form-item label="列数">
          <el-input-number v-model="plateForm.cols" :min="1" :max="24" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreatePlate = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePlate">创建</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Grid, Plus, Edit, Delete, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { experimentApi } from '../../api'

const route = useRoute()
const userStore = useUserStore()
const experimentId = Number(route.params.id)
const experiment = ref<any>(null)
const plates = ref<any[]>([])
const showCreatePlate = ref(false)
const plateForm = ref({ name: '', rows: 8, cols: 12 })

async function loadData() {
  const expRes = await experimentApi.listExperiments()
  experiment.value = expRes.data.find((e: any) => e.id === experimentId)
  const plRes = await experimentApi.listPlates(experimentId)
  plates.value = plRes.data
}

async function handleCreatePlate() {
  if (!plateForm.value.name) return ElMessage.warning('请输入孔板名称')
  await experimentApi.createPlate(experimentId, plateForm.value.name, plateForm.value.rows, plateForm.value.cols)
  ElMessage.success('孔板创建成功')
  showCreatePlate.value = false
  plateForm.value = { name: '', rows: 8, cols: 12 }
  await loadData()
}

async function handleDeletePlate(id: number) {
  await experimentApi.deletePlate(id)
  ElMessage.success('已删除')
  await loadData()
}

onMounted(loadData)
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
