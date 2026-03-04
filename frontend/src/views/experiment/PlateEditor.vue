<template>
  <el-container class="page-container">
    <el-header class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push(`/experiment/${experimentId}`)" circle />
        <el-icon :size="28" color="#fff"><Monitor /></el-icon>
        <span class="brand">孔板编辑</span>
      </div>
      <div class="header-right">
        <el-button type="success" @click="handleSave" :loading="saving">
          <el-icon><Check /></el-icon> 保存数据
        </el-button>
      </div>
    </el-header>

    <el-main class="page-main">
      <!-- Batch Fill Tool -->
      <el-card style="margin-bottom: 16px">
        <template #header>
          <span class="card-title"><el-icon><MagicStick /></el-icon> 批量填充工具</span>
        </template>
        <el-form :inline="true" :model="batchForm">
          <el-form-item label="化合物">
            <el-input v-model="batchForm.compound" placeholder="化合物名称" style="width:140px" />
          </el-form-item>
          <el-form-item label="浓度">
            <el-input-number v-model="batchForm.concentration" :precision="4" :step="0.1" :min="0" style="width:140px" />
          </el-form-item>
          <el-form-item label="单位">
            <el-select v-model="batchForm.unit" style="width:80px">
              <el-option label="μM" value="μM" />
              <el-option label="nM" value="nM" />
              <el-option label="mM" value="mM" />
            </el-select>
          </el-form-item>
          <el-form-item label="批次">
            <el-input v-model="batchForm.batch" placeholder="如 Batch-01" style="width:120px" />
          </el-form-item>
          <el-form-item label="值">
            <el-input-number v-model="batchForm.value" :precision="4" style="width:140px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyBatch" :disabled="selectedCells.length === 0">
              填充选中 ({{ selectedCells.length }})
            </el-button>
            <el-button @click="clearSelection">清除选择</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Plate Grid -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span class="card-title"><el-icon><Grid /></el-icon> 孔板 ({{ plateRows }}×{{ plateCols }})</span>
            <el-tag>点击格子选择，Shift+点击批量选择</el-tag>
          </div>
        </template>

        <div class="plate-grid-wrapper">
          <table class="plate-grid">
            <thead>
              <tr>
                <th class="corner-cell"></th>
                <th v-for="c in plateCols" :key="c" class="col-header" @click="selectColumn(c - 1)">{{ c }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in plateRows" :key="r">
                <td class="row-header" @click="selectRow(r - 1)">{{ String.fromCharCode(64 + r) }}</td>
                <td
                  v-for="c in plateCols" :key="c"
                  :class="['well-cell', {
                    'selected': isSelected(r - 1, c - 1),
                    'filled': getWell(r - 1, c - 1)?.compound_name,
                    'has-value': getWell(r - 1, c - 1)?.value != null
                  }]"
                  @click="toggleCell(r - 1, c - 1, $event)"
                  @dblclick="editCell(r - 1, c - 1)"
                >
                  <div class="well-content" v-if="getWell(r - 1, c - 1)?.compound_name">
                    <div class="well-compound">{{ getWell(r - 1, c - 1)?.compound_name }}</div>
                    <div class="well-conc">{{ getWell(r - 1, c - 1)?.concentration }}{{ getWell(r - 1, c - 1)?.concentration_unit }}</div>
                    <div class="well-value" v-if="getWell(r - 1, c - 1)?.value != null">{{ getWell(r - 1, c - 1)?.value }}</div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-card>

      <!-- Single Cell Editor Dialog -->
      <el-dialog v-model="showCellEditor" title="编辑孔位" width="400px">
        <el-form :model="cellForm" label-width="80px">
          <el-form-item label="位置">
            <el-tag>{{ String.fromCharCode(65 + cellForm.row) }}{{ cellForm.col + 1 }}</el-tag>
          </el-form-item>
          <el-form-item label="化合物">
            <el-input v-model="cellForm.compound" placeholder="化合物名称" />
          </el-form-item>
          <el-form-item label="浓度">
            <el-input-number v-model="cellForm.concentration" :precision="4" :step="0.1" :min="0" style="width:100%" />
          </el-form-item>
          <el-form-item label="单位">
            <el-select v-model="cellForm.unit" style="width:100%">
              <el-option label="μM" value="μM" />
              <el-option label="nM" value="nM" />
              <el-option label="mM" value="mM" />
            </el-select>
          </el-form-item>
          <el-form-item label="批次">
            <el-input v-model="cellForm.batch" placeholder="批次号" />
          </el-form-item>
          <el-form-item label="实验值">
            <el-input-number v-model="cellForm.value" :precision="4" style="width:100%" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCellEditor = false">取消</el-button>
          <el-button type="danger" @click="clearCell">清除</el-button>
          <el-button type="primary" @click="saveCellForm">确定</el-button>
        </template>
      </el-dialog>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Grid, Check, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { experimentApi } from '../../api'

const route = useRoute()
const experimentId = Number(route.params.id)
const plateId = Number(route.params.plateId)

const plateRows = ref(8)
const plateCols = ref(12)
const saving = ref(false)

interface WellInfo {
  compound_name?: string
  concentration?: number
  concentration_unit: string
  batch?: string
  value?: number
}

const wellsMap = reactive<Record<string, WellInfo>>({})
const selectedCells = ref<{row: number, col: number}[]>([])
const lastSelected = ref<{row: number, col: number} | null>(null)
const showCellEditor = ref(false)
const cellForm = reactive({ row: 0, col: 0, compound: '', concentration: 0, unit: 'μM', batch: '', value: 0 as number | undefined })
const batchForm = reactive({ compound: '', concentration: 0, unit: 'μM', batch: '', value: undefined as number | undefined })

function wellKey(r: number, c: number) { return `${r}_${c}` }

function getWell(r: number, c: number): WellInfo | undefined {
  return wellsMap[wellKey(r, c)]
}

function isSelected(r: number, c: number): boolean {
  return selectedCells.value.some(s => s.row === r && s.col === c)
}

function toggleCell(r: number, c: number, event: MouseEvent) {
  if (event.shiftKey && lastSelected.value) {
    const minR = Math.min(lastSelected.value.row, r)
    const maxR = Math.max(lastSelected.value.row, r)
    const minC = Math.min(lastSelected.value.col, c)
    const maxC = Math.max(lastSelected.value.col, c)
    for (let ri = minR; ri <= maxR; ri++) {
      for (let ci = minC; ci <= maxC; ci++) {
        if (!isSelected(ri, ci)) {
          selectedCells.value.push({ row: ri, col: ci })
        }
      }
    }
  } else {
    const idx = selectedCells.value.findIndex(s => s.row === r && s.col === c)
    if (idx >= 0) {
      selectedCells.value.splice(idx, 1)
    } else {
      selectedCells.value.push({ row: r, col: c })
    }
  }
  lastSelected.value = { row: r, col: c }
}

function selectRow(r: number) {
  for (let c = 0; c < plateCols.value; c++) {
    if (!isSelected(r, c)) selectedCells.value.push({ row: r, col: c })
  }
}

function selectColumn(c: number) {
  for (let r = 0; r < plateRows.value; r++) {
    if (!isSelected(r, c)) selectedCells.value.push({ row: r, col: c })
  }
}

function clearSelection() {
  selectedCells.value = []
}

function applyBatch() {
  for (const cell of selectedCells.value) {
    const key = wellKey(cell.row, cell.col)
    wellsMap[key] = {
      compound_name: batchForm.compound || undefined,
      concentration: batchForm.concentration || undefined,
      concentration_unit: batchForm.unit,
      batch: batchForm.batch || undefined,
      value: batchForm.value,
    }
  }
  ElMessage.success(`已填充 ${selectedCells.value.length} 个孔位`)
  selectedCells.value = []
}

function editCell(r: number, c: number) {
  const w = getWell(r, c)
  cellForm.row = r
  cellForm.col = c
  cellForm.compound = w?.compound_name || ''
  cellForm.concentration = w?.concentration || 0
  cellForm.unit = w?.concentration_unit || 'μM'
  cellForm.batch = w?.batch || ''
  cellForm.value = w?.value
  showCellEditor.value = true
}

function saveCellForm() {
  const key = wellKey(cellForm.row, cellForm.col)
  wellsMap[key] = {
    compound_name: cellForm.compound || undefined,
    concentration: cellForm.concentration || undefined,
    concentration_unit: cellForm.unit,
    batch: cellForm.batch || undefined,
    value: cellForm.value,
  }
  showCellEditor.value = false
}

function clearCell() {
  const key = wellKey(cellForm.row, cellForm.col)
  delete wellsMap[key]
  showCellEditor.value = false
}

async function handleSave() {
  saving.value = true
  try {
    const wells = []
    for (let r = 0; r < plateRows.value; r++) {
      for (let c = 0; c < plateCols.value; c++) {
        const w = getWell(r, c)
        wells.push({
          row_index: r,
          col_index: c,
          compound_name: w?.compound_name || null,
          concentration: w?.concentration || null,
          concentration_unit: w?.concentration_unit || 'μM',
          batch: w?.batch || null,
          value: w?.value ?? null,
        })
      }
    }
    await experimentApi.batchUpdateWells(plateId, wells)
    ElMessage.success('保存成功')
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function loadWells() {
  try {
    const res = await experimentApi.getWells(plateId)
    plateRows.value = res.data.plate.rows
    plateCols.value = res.data.plate.cols
    for (const w of res.data.wells) {
      if (w.compound_name) {
        wellsMap[wellKey(w.row_index, w.col_index)] = {
          compound_name: w.compound_name,
          concentration: w.concentration ? parseFloat(w.concentration) : undefined,
          concentration_unit: w.concentration_unit,
          batch: w.batch,
          value: w.value != null ? parseFloat(w.value) : undefined,
        }
      }
    }
  } catch (e) {
    ElMessage.error('加载数据失败')
  }
}

onMounted(loadWells)
</script>

<style scoped>
.page-container { height: 100vh; background: #f0f2f5; }
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.brand { color: #fff; font-size: 20px; font-weight: 600; }
.page-main { padding: 16px; overflow-y: auto; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }

.plate-grid-wrapper { overflow-x: auto; }

.plate-grid {
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
}

.plate-grid th, .plate-grid td {
  border: 1.5px solid #dcdfe6;
  text-align: center;
  padding: 0;
}

.corner-cell { width: 36px; height: 28px; background: #f5f7fa; }
.col-header { height: 28px; background: #f5f7fa; font-size: 12px; font-weight: 600; color: #606266; cursor: pointer; }
.col-header:hover { background: #e8eaf0; }
.row-header { width: 36px; background: #f5f7fa; font-size: 12px; font-weight: 600; color: #606266; cursor: pointer; }
.row-header:hover { background: #e8eaf0; }

.well-cell {
  height: 68px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
  vertical-align: top;
}

.well-cell:hover { background: #ecf5ff; }
.well-cell.selected { background: #d9ecff; border-color: #409eff !important; }
.well-cell.filled { background: #f0f9eb; }
.well-cell.has-value { background: #e8f5e9; }
.well-cell.selected.filled { background: #b3d8ff; }

.well-content {
  padding: 2px;
  font-size: 10px;
  line-height: 1.3;
  overflow: hidden;
}

.well-compound { font-weight: 600; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.well-conc { color: #909399; }
.well-value { color: #67c23a; font-weight: 600; margin-top: 2px; }
</style>
