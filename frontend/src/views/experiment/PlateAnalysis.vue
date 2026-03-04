<template>
  <el-container class="page-container">
    <el-header class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="$router.push(`/experiment/${experimentId}`)" circle />
        <el-icon :size="28" color="#fff"><DataAnalysis /></el-icon>
        <span class="brand">数据分析</span>
      </div>
      <div class="header-right">
        <span class="username" style="color:#fff">{{ userStore.user?.username }}</span>
      </div>
    </el-header>

    <el-main class="page-main">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- Tab 1: Raw Data -->
        <el-tab-pane label="原始数据" name="raw">
          <el-table :data="rawData" stripe border style="width:100%" max-height="500">
            <el-table-column label="孔位" width="70">
              <template #default="{ row }">{{ String.fromCharCode(65 + row.row_index) }}{{ row.col_index + 1 }}</template>
            </el-table-column>
            <el-table-column prop="compound_name" label="化合物" width="140" />
            <el-table-column label="浓度" width="120">
              <template #default="{ row }">{{ row.concentration }} {{ row.concentration_unit }}</template>
            </el-table-column>
            <el-table-column prop="batch" label="批次" width="100" />
            <el-table-column prop="value" label="实验值" width="120" />
          </el-table>
        </el-tab-pane>

        <!-- Tab 2: Grouped Statistics -->
        <el-tab-pane label="统计汇总" name="stats">
          <el-table :data="groupedData" stripe border style="width:100%">
            <el-table-column prop="compound_name" label="化合物" width="140" />
            <el-table-column label="浓度" width="120">
              <template #default="{ row }">{{ row.concentration }} {{ row.concentration_unit }}</template>
            </el-table-column>
            <el-table-column prop="count" label="样本数" width="80" />
            <el-table-column label="平均值" width="120">
              <template #default="{ row }">{{ row.avg_value?.toFixed(4) }}</template>
            </el-table-column>
            <el-table-column label="最大值" width="120">
              <template #default="{ row }">{{ row.max_value?.toFixed(4) }}</template>
            </el-table-column>
            <el-table-column label="最小值" width="120">
              <template #default="{ row }">{{ row.min_value?.toFixed(4) }}</template>
            </el-table-column>
            <el-table-column label="标准差" width="120">
              <template #default="{ row }">{{ row.std_value?.toFixed(4) ?? 'N/A' }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab 3: Dose-Response Curve -->
        <el-tab-pane label="剂量-反应曲线" name="curve">
          <div v-if="curveData.length === 0" class="empty-hint">
            <el-empty description="暂无拟合数据，请确保孔板有足够的数据（每个化合物至少4个浓度点）" />
          </div>
          <div v-for="compound in curveData" :key="compound.compound" style="margin-bottom: 40px">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon><TrendCharts /></el-icon>
                    {{ compound.compound }}
                  </span>
                  <div v-if="compound.fit_success">
                    <el-tag type="success" style="margin-right:8px">拟合成功</el-tag>
                    <el-tag type="warning">IC50 = {{ compound.ic50?.toFixed(4) }} {{ compound.data_points[0]?.concentration_unit || 'μM' }}</el-tag>
                    <el-tag style="margin-left:8px">R² = {{ compound.fit_params?.r_squared?.toFixed(4) }}</el-tag>
                  </div>
                  <el-tag v-else type="danger">数据点不足，无法拟合</el-tag>
                </div>
              </template>
              <div :ref="(el: any) => setChartRef(compound.compound, el)" class="chart-container"></div>

              <el-descriptions v-if="compound.fit_success" border :column="4" style="margin-top:16px">
                <el-descriptions-item label="Bottom (A)">{{ compound.fit_params?.bottom?.toFixed(4) }}</el-descriptions-item>
                <el-descriptions-item label="Hill Slope (B)">{{ compound.fit_params?.hill_slope?.toFixed(4) }}</el-descriptions-item>
                <el-descriptions-item label="IC50 (C)">{{ compound.fit_params?.ic50?.toFixed(4) }}</el-descriptions-item>
                <el-descriptions-item label="Top (D)">{{ compound.fit_params?.top?.toFixed(4) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, DataAnalysis, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { experimentApi } from '../../api'
import * as echarts from 'echarts'

const route = useRoute()
const userStore = useUserStore()
const experimentId = Number(route.params.id)
const plateId = Number(route.params.plateId)

const activeTab = ref('stats')
const rawData = ref<any[]>([])
const groupedData = ref<any[]>([])
const curveData = ref<any[]>([])

const chartRefs: Record<string, HTMLElement | null> = {}
const chartInstances: Record<string, echarts.ECharts> = {}

function setChartRef(name: string, el: HTMLElement | null) {
  if (el) chartRefs[name] = el
}

async function loadStatistics() {
  try {
    const res = await experimentApi.getStatistics(plateId)
    rawData.value = res.data.raw_data
    groupedData.value = res.data.grouped
  } catch (e) {
    ElMessage.error('加载统计数据失败')
  }
}

async function loadCurveFit() {
  try {
    const res = await experimentApi.getCurveFit(plateId)
    curveData.value = res.data.compounds
  } catch (e) {
    ElMessage.error('加载拟合数据失败')
  }
}

function renderCharts() {
  for (const compound of curveData.value) {
    const el = chartRefs[compound.compound]
    if (!el) continue

    const existing = chartInstances[compound.compound]
    if (existing) {
      existing.dispose()
    }

    const chart = echarts.init(el)
    chartInstances[compound.compound] = chart

    const scatterData = compound.data_points.map((p: any) => [p.concentration, p.inhibition])

    const option: echarts.EChartsOption = {
      title: {
        text: `${compound.compound} — 剂量-反应曲线`,
        left: 'center',
        textStyle: { fontSize: 14 },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (Array.isArray(params.value)) {
            return `浓度: ${params.value[0]}<br/>抑制率: ${params.value[1].toFixed(2)}%`
          }
          return ''
        },
      },
      xAxis: {
        type: 'log',
        name: '浓度 (μM)',
        nameLocation: 'middle',
        nameGap: 30,
        min: Math.min(...compound.data_points.map((p: any) => p.concentration)) / 2,
        max: Math.max(...compound.data_points.map((p: any) => p.concentration)) * 2,
      },
      yAxis: {
        type: 'value',
        name: '抑制率 (%)',
        nameLocation: 'middle',
        nameGap: 45,
      },
      series: [
        {
          name: '实验数据',
          type: 'scatter',
          data: scatterData,
          symbolSize: 10,
          itemStyle: { color: '#409eff' },
        },
      ] as any[],
    }

    if (compound.fit_success && compound.fit_curve?.length > 0) {
      const fitLine = compound.fit_curve.map((p: any) => [p.concentration, p.inhibition])
      ;(option.series as any[]).push({
        name: '4PL拟合曲线',
        type: 'line',
        data: fitLine,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#e6a23c', width: 2 },
        itemStyle: { color: '#e6a23c' },
      })

      if (compound.ic50) {
        ;(option.series as any[]).push({
          name: 'IC50',
          type: 'scatter',
          data: [[compound.ic50, 50]],
          symbolSize: 14,
          symbol: 'diamond',
          itemStyle: { color: '#f56c6c' },
          label: {
            show: true,
            formatter: `IC50=${compound.ic50.toFixed(2)}`,
            position: 'top',
            color: '#f56c6c',
            fontWeight: 'bold',
          },
        })
      }

      option.legend = {
        bottom: 0,
        data: ['实验数据', '4PL拟合曲线', 'IC50'],
      }
    }

    chart.setOption(option)
  }
}

watch(activeTab, async (val) => {
  if (val === 'curve') {
    await nextTick()
    setTimeout(renderCharts, 100)
  }
})

onMounted(async () => {
  await Promise.all([loadStatistics(), loadCurveFit()])
})
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
.card-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.card-title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.chart-container { width: 100%; height: 400px; }
.empty-hint { padding: 40px 0; }
</style>
