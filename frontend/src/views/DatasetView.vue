<template>
  <div class="page-root">
    <!-- Page Header + Dataset Loader -->
    <header class="page-header pb-4 border-b border-border-1">
      <div class="flex items-end gap-4">
        <div>
          <h1 class="page-title">数据集管理</h1>
          <p class="page-sub">一致性体检 · 标注查看器 · 数据分析 · 集合拆分</p>
        </div>
        <div class="flex-1 max-w-xl">
          <el-input
            v-model="rootDir"
            placeholder="数据集根目录路径（含 images/ + labels/ + classes.txt）"
            @change="loadDataset"
            size="small"
          >
            <template #prefix><FolderOpen :size="13" class="text-ink-4"/></template>
            <template #append>
              <el-button @click="loadDataset" :loading="loading" size="small">加载</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </header>

    <!-- ── Loading placeholder ──────────────────────────── -->
    <div v-if="!info?.is_valid" class="flex-1 flex flex-col items-center justify-center gap-4 text-ink-4">
      <div class="w-20 h-20 rounded-3xl bg-bg-3 border border-border-1 flex items-center justify-center">
        <Database :size="36" class="text-ink-4"/>
      </div>
      <div class="text-sm font-medium">请先输入并加载数据集</div>
      <div class="text-xs text-ink-4">支持 YOLO 格式：images/ + labels/ + classes.txt</div>
    </div>

    <!-- ── Dashboard ─────────────────────────────────────── -->
    <div v-else class="flex-1 overflow-hidden flex flex-col">

      <!-- ── Bento Grid top ─────────────────────────────── -->
      <div class="flex-shrink-0 px-6 pt-4 pb-0 grid grid-cols-12 gap-4">

        <!-- Stat Cards (left 5 cols) -->
        <div class="col-span-5 grid grid-cols-5 gap-3">
          <div v-for="s in statCards" :key="s.label"
            class="bento-card relative overflow-hidden p-3 flex flex-col gap-1"
            :style="`--c:${s.color}`"
          >
            <div class="absolute top-0 left-0 right-0 h-0.5 rounded-t-[14px]" :style="`background:${s.color}`"></div>
            <div class="text-xl font-extrabold leading-none" :style="`color:${s.color}`">{{ s.val }}</div>
            <div class="text-[10px] text-ink-4 uppercase tracking-wider">{{ s.label }}</div>
          </div>
        </div>

        <!-- Class Distribution (right 7 cols) -->
        <div class="col-span-7 bento-card p-4">
          <div class="text-[10px] text-ink-4 uppercase tracking-wider font-semibold mb-2">类别分布</div>
          <div class="space-y-1.5 max-h-24 overflow-y-auto scroll-y">
            <div v-for="(c, i) in info.classes" :key="i" class="flex items-center gap-2">
              <div class="text-[11px] text-ink-3 w-24 truncate flex-shrink-0">{{ i }}: {{ c }}</div>
              <div class="flex-1 h-2 bg-bg-4 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500"
                  :style="`width:${getClassPct(i)}%;background:${colors[i%colors.length]}`"></div>
              </div>
              <div class="text-[11px] font-semibold w-8 text-right" :style="`color:${colors[i%colors.length]}`">
                {{ classCounts[i] || 0 }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Tab area ───────────────────────────────────── -->
      <div class="tab-nav mt-4">
        <button v-for="tab in tabs" :key="tab.id"
          class="tab-btn" :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >{{ tab.label }}</button>
      </div>

      <div class="flex-1 overflow-hidden">

        <!-- ══ Sanity Check ════════════════════════════════ -->
        <div v-show="activeTab === 'sanity'" class="h-full overflow-y-auto p-6 scroll-y">
          <div class="flex items-center gap-3 mb-4">
            <el-button type="primary" :loading="checking" :disabled="!info?.is_valid" @click="startCheck">
              🔍 开始体检
            </el-button>
            <el-button type="danger" :disabled="!fixableCount" @click="fixIssues">
              🔧 删除孤立标注（{{ fixableCount }}）
            </el-button>
            <el-progress v-if="checking" :percentage="checkPercent" class="w-48" :show-text="false"/>
            <span class="text-xs px-3 py-1 rounded-full"
              :class="checkStatus.startsWith('✅') ? 'text-em-green bg-em-green/10' : checkStatus.startsWith('⚠️') ? 'text-em-yellow bg-em-yellow/10' : 'text-ink-3 bg-bg-4'"
            >{{ checkStatus || '尚未体检' }}</span>
          </div>

          <!-- Issue badges -->
          <div v-if="Object.keys(issueGroups).length" class="flex gap-2 flex-wrap mb-4">
            <div v-for="(cnt, cat) in issueGroups" :key="cat"
              class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border"
              :style="`background:${catColor(cat)}18;border-color:${catColor(cat)}44;color:${catColor(cat)}`"
            >
              <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :style="`background:${catColor(cat)}`"></span>
              {{ cat }} <b>{{ cnt }}</b>
            </div>
          </div>

          <el-table v-if="issues.length" :data="issues" height="360" size="small">
            <el-table-column prop="category" label="类型" width="130">
              <template #default="{row}">
                <span class="text-[11px] px-2 py-0.5 rounded-full border"
                  :style="`color:${catColor(row.category)};border-color:${catColor(row.category)}44;background:${catColor(row.category)}15`">
                  {{ row.category }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="filename" label="文件名"/>
            <el-table-column prop="detail" label="说明"/>
          </el-table>
          <div v-else-if="checkDone" class="text-center text-em-green py-10 text-sm">✅  体检通过，数据集完全一致</div>
        </div>

        <!-- ══ Annotation Viewer ═══════════════════════════ -->
        <div v-show="activeTab === 'viewer'" class="h-full flex overflow-hidden">
          <div class="w-52 flex-shrink-0 bg-bg-2 border-r border-border-1 flex flex-col">
            <div class="px-3 py-2 text-[11px] text-ink-4 uppercase tracking-wider font-semibold border-b border-border-1 flex justify-between items-center">
              图片列表
              <span class="bg-bg-4 text-accent px-2 py-0.5 rounded-full text-[10px]">{{ imageList.length }}</span>
            </div>
            <div class="flex-1 overflow-y-auto scroll-y">
              <div v-for="(img, i) in imageList" :key="i"
                class="px-3 py-2 text-xs cursor-pointer border-b border-border-1 truncate transition-colors"
                :class="currentIdx === i ? 'bg-accent/10 text-accent border-l-2 border-l-accent' : 'text-ink-3 hover:bg-bg-3 hover:text-ink-2'"
                @click="selectImage(i)"
              >{{ img.split('/').pop() }}</div>
            </div>
            <div class="flex items-center justify-between px-3 py-2 border-t border-border-1">
              <el-button size="small" :disabled="currentIdx <= 0" @click="selectImage(currentIdx-1)">◀</el-button>
              <span class="text-xs text-ink-3">{{ currentIdx >= 0 ? `${currentIdx+1}/${imageList.length}` : '—' }}</span>
              <el-button size="small" :disabled="currentIdx >= imageList.length-1" @click="selectImage(currentIdx+1)">▶</el-button>
            </div>
          </div>
          <div class="flex-1 p-4 overflow-auto flex flex-col gap-2">
            <div v-if="currentImg" class="text-xs text-ink-3">
              {{ currentImg.split('/').pop() }} &nbsp;·&nbsp; <span class="text-accent">{{ currentLabels.length }}</span> 个标注框
            </div>
            <canvas ref="canvasRef" class="max-w-full rounded-xl border border-border-1"/>
            <div v-if="!currentImg" class="flex-1 flex items-center justify-center text-ink-4 text-sm">← 从左侧选择图片查看标注</div>
          </div>
        </div>

        <!-- ══ Analytics ═══════════════════════════════════ -->
        <div v-show="activeTab === 'analytics'" class="h-full overflow-y-auto p-6 scroll-y">
          <div class="flex items-center gap-3 mb-4">
            <el-button type="primary" :disabled="!info?.is_valid" :loading="analyzing" @click="runAnalysis">
              📊 开始分析
            </el-button>
            <span v-if="analyticsDone" class="text-xs text-em-green bg-em-green/10 px-3 py-1 rounded-full">{{ analyticsStatus }}</span>
          </div>

          <div v-if="analyticsData">
            <!-- Metric cards -->
            <div class="grid grid-cols-4 gap-4 mb-6">
              <div class="bento-card relative overflow-hidden p-4" style="--mg:var(--grad-accent)">
                <div class="absolute top-0 left-0 right-0 h-0.5 rounded-t-[14px]" style="background:var(--grad-accent)"></div>
                <div class="text-2xl font-extrabold text-ink-1">{{ analyticsData.total_instances?.toLocaleString() }}</div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mt-1">总标注框数</div>
              </div>
              <div class="bento-card relative overflow-hidden p-4">
                <div class="absolute top-0 left-0 right-0 h-0.5 rounded-t-[14px]" style="background:var(--grad-green)"></div>
                <div class="text-2xl font-extrabold text-ink-1">{{ analyticsData.avg_width }}</div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mt-1">平均框宽（归一化）</div>
              </div>
              <div class="bento-card relative overflow-hidden p-4">
                <div class="absolute top-0 left-0 right-0 h-0.5 rounded-t-[14px]" style="background:var(--grad-blue)"></div>
                <div class="text-2xl font-extrabold text-ink-1">{{ analyticsData.avg_height }}</div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mt-1">平均框高（归一化）</div>
              </div>
              <div class="bento-card relative overflow-hidden p-4"
                :style="`--top-col:${analyticsData.long_tail_warning ? 'var(--grad-orange)' : 'var(--grad-green)'}`">
                <div class="absolute top-0 left-0 right-0 h-0.5 rounded-t-[14px]" style="background:var(--top-col)"></div>
                <div class="text-xl font-extrabold text-ink-1">{{ analyticsData.long_tail_warning ? '⚠️ 长尾' : '✅ 均衡' }}</div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mt-1">类别分布</div>
              </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-2 gap-4">
              <div class="bento-card p-4">
                <div class="text-[10px] text-ink-4 uppercase tracking-wider font-semibold mb-3">类别分布（实例数）</div>
                <v-chart v-if="barOption" :option="barOption" style="height:220px" autoresize/>
              </div>
              <div class="bento-card p-4">
                <div class="text-[10px] text-ink-4 uppercase tracking-wider font-semibold mb-3">标注框尺寸散点图（W×H 归一化）</div>
                <v-chart v-if="scatterOption" :option="scatterOption" style="height:220px" autoresize/>
              </div>
            </div>
          </div>
          <div v-else-if="!analyzing" class="flex-1 flex items-center justify-center text-ink-4 text-sm py-20">
            点击「开始分析」生成数据报表
          </div>
        </div>

        <!-- ══ Split Dataset ═══════════════════════════════ -->
        <div v-show="activeTab === 'split'" class="h-full overflow-y-auto p-6 scroll-y">
          <!-- Three-color ratio bar -->
          <div class="bento-card p-5 mb-4">
            <div class="text-[10px] text-ink-4 uppercase tracking-wider font-semibold mb-3">数据集拆分比例</div>

            <!-- Visual ratio bar -->
            <div class="h-8 rounded-xl overflow-hidden flex mb-4 border border-border-1">
              <div class="h-full transition-all duration-300 flex items-center justify-center text-xs font-bold text-white/90"
                :style="`width:${ratios.train.val}%;background:${ratios.train.color}`">
                {{ ratios.train.val > 5 ? `Train ${ratios.train.val}%` : '' }}
              </div>
              <div class="h-full transition-all duration-300 flex items-center justify-center text-xs font-bold text-white/90"
                :style="`width:${ratios.val.val}%;background:${ratios.val.color}`">
                {{ ratios.val.val > 5 ? `Val ${ratios.val.val}%` : '' }}
              </div>
              <div class="h-full transition-all duration-300 flex items-center justify-center text-xs font-bold text-white/90"
                :style="`width:${ratios.test.val}%;background:${ratios.test.color}`">
                {{ ratios.test.val > 5 ? `Test ${ratios.test.val}%` : '' }}
              </div>
            </div>

            <!-- Sliders -->
            <div class="grid grid-cols-3 gap-4">
              <div v-for="(r, key) in ratios" :key="key">
                <div class="flex justify-between mb-1.5">
                  <span class="text-xs text-ink-3 font-medium">{{ r.label }}</span>
                  <span class="text-xs font-bold" :style="`color:${r.color}`">{{ r.val }}%</span>
                </div>
                <input type="range" v-model.number="r.val" min="0" max="100" step="1"
                  class="ratio-slider w-full" :style="`--sc:${r.color}`"
                  @input="clampRatios(key)"/>
              </div>
            </div>

            <div class="mt-2 text-right">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                :class="ratioOk ? 'text-em-green bg-em-green/10' : 'text-em-red bg-em-red/10'"
              >合计 {{ totalRatio }}%</span>
            </div>
          </div>

          <!-- Config grid -->
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="col-span-2">
              <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">输出目录（留空 = 数据集 /split）</div>
              <el-input v-model="splitOutput" placeholder="留空自动生成" size="small"/>
            </div>
            <div>
              <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">随机种子</div>
              <el-input-number v-model="splitSeed" :min="0" size="small" style="width:100%"/>
            </div>
          </div>
          <div class="flex items-center gap-4 mb-4">
            <div class="text-xs text-ink-3">文件操作</div>
            <el-radio-group v-model="splitMove" size="small">
              <el-radio-button :label="false">复制</el-radio-button>
              <el-radio-button :label="true">移动</el-radio-button>
            </el-radio-group>
          </div>

          <div class="flex items-center gap-4 mb-4">
            <el-button type="primary" size="default" :loading="splitting" :disabled="!ratioOk" @click="startSplit">
              ✂️  开始拆分
            </el-button>
            <el-progress v-if="splitting" :percentage="splitPercent" class="w-48" :show-text="false"/>
            <span v-if="splitStatus" class="text-xs"
              :class="splitStatus.startsWith('✅') ? 'text-em-green' : 'text-ink-3'">{{ splitStatus }}</span>
          </div>

          <!-- YAML preview -->
          <div v-if="yamlContent" class="bento-card overflow-hidden">
            <div class="px-4 py-2.5 border-b border-border-1 text-[11px] text-ink-4 font-semibold uppercase tracking-wider">📄 dataset.yaml</div>
            <pre class="px-4 py-4 font-mono text-[13px] text-em-green leading-relaxed">{{ yamlContent }}</pre>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { datasetAPI } from '../api'
import { FolderOpen, Database } from 'lucide-vue-next'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, ScatterChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
use([BarChart, ScatterChart, GridComponent, TooltipComponent, CanvasRenderer])

const colors = ['#6366f1','#10b981','#f97316','#8b5cf6','#fbbf24','#3b82f6','#ec4899','#14b8a6','#f43f5e','#84cc16']

// ── Dataset load ─────────────────────────────────────────
const rootDir = ref('')
const info = ref(null)
const loading = ref(false)
const activeTab = ref('sanity')
const tabs = [
  { id: 'sanity',    label: '🔍  一致性体检' },
  { id: 'viewer',    label: '👁  标注查看器' },
  { id: 'analytics', label: '📊  数据分析' },
  { id: 'split',     label: '✂️  拆分数据集' },
]

async function loadDataset() {
  if (!rootDir.value.trim()) return
  loading.value = true
  try {
    const r = await datasetAPI.load(rootDir.value.trim())
    if (r.success) {
      info.value = r.data
      ElMessage.success(`已加载：${r.data.total_images} 张图片，${r.data.classes.length} 个类别`)
      const lr = await datasetAPI.getImageList(rootDir.value.trim())
      if (lr.success) imageList.value = lr.data
    } else { ElMessage.error(r.error) }
  } catch (e) { ElMessage.error(String(e)) }
  finally { loading.value = false }
}

// Top stat cards
const statCards = computed(() => info.value ? [
  { label: '总图片',  val: info.value.total_images,    color: '#6366f1' },
  { label: '已标注',  val: info.value.labeled_images,  color: '#10b981' },
  { label: '未标注',  val: info.value.unlabeled_images,color: '#f97316' },
  { label: '类别数',  val: info.value.classes.length,  color: '#8b5cf6' },
  { label: '标注框',  val: info.value.total_instances, color: '#fbbf24' },
] : [])

// Class counts from analytics (if available)
const classCounts = ref({})
const classMaxCount = computed(() => Math.max(...Object.values(classCounts.value), 1))
function getClassPct(idx) {
  const c = classCounts.value[idx] || 0
  return Math.round(c / classMaxCount.value * 100)
}

// ── Sanity Check ─────────────────────────────────────────
const issues = ref([])
const checkPercent = ref(0)
const checking = ref(false)
const checkDone = ref(false)
const checkStatus = ref('')
const issueGroups = computed(() => {
  const g = {}
  issues.value.forEach(i => g[i.category] = (g[i.category]||0)+1)
  return g
})
const fixableCount = computed(() => issues.value.filter(i => ['有标注无图','空标注'].includes(i.category)).length)

function catColor(cat) {
  return { '有图无标注':'#f97316','有标注无图':'#ef4444','空标注':'#fbbf24','类别越界':'#6366f1' }[cat]||'#9898b8'
}

function startCheck() {
  issues.value = []; checkPercent.value = 0; checking.value = true; checkDone.value = false; checkStatus.value = '体检中…'
  datasetAPI.sanityCheck(
    info.value.root_dir,
    (ev) => { if (ev.type === 'progress') checkPercent.value = ev.percent },
    (ev) => { issues.value = ev.issues||[]; checking.value = false; checkDone.value = true; checkStatus.value = ev.total_issues ? `⚠️  发现 ${ev.total_issues} 个问题` : '✅  体检通过' },
    (err) => { checkStatus.value = `❌  ${err}`; checking.value = false }
  )
}
async function fixIssues() {
  const r = await datasetAPI.fixIssues(issues.value)
  if (r.success) { ElMessage.success(`已删除 ${r.data.success} 个文件`); startCheck() }
}

// ── Annotation Viewer ─────────────────────────────────────
const imageList = ref([])
const currentIdx = ref(-1)
const currentImg = ref('')
const currentLabels = ref([])
const canvasRef = ref(null)

async function selectImage(idx) {
  currentIdx.value = idx
  currentImg.value = imageList.value[idx]
  const r = await datasetAPI.getLabel(currentImg.value, info.value.root_dir)
  currentLabels.value = r.success ? r.data : []
  await drawCanvas(r.success ? r.classes : info.value?.classes || [])
}

async function drawCanvas(classes) {
  if (!currentImg.value || !canvasRef.value) return
  const imgR = await datasetAPI.getImage(currentImg.value)
  if (!imgR.success) return
  const image = new Image()
  image.src = imgR.data
  image.onload = () => {
    const canvas = canvasRef.value
    const w = canvas.parentElement.clientWidth - 32
    const scale = w / image.width
    canvas.width = w; canvas.height = image.height * scale
    const ctx = canvas.getContext('2d')
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height)
    currentLabels.value.forEach(lbl => {
      const color = colors[lbl.class_id % colors.length]
      const x = (lbl.cx - lbl.w/2) * canvas.width
      const y = (lbl.cy - lbl.h/2) * canvas.height
      const bw = lbl.w * canvas.width; const bh = lbl.h * canvas.height
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.strokeRect(x, y, bw, bh)
      const label = `${lbl.class_id}: ${classes?.[lbl.class_id] || lbl.class_id}`
      ctx.font = '12px Inter, sans-serif'
      const tw = ctx.measureText(label).width + 6
      ctx.fillStyle = color; ctx.globalAlpha = 0.85; ctx.fillRect(x, Math.max(0, y-18), tw, 18)
      ctx.globalAlpha = 1; ctx.fillStyle = '#fff'; ctx.fillText(label, x+3, Math.max(12, y-4))
    })
  }
}

// ── Analytics ──────────────────────────────────────────────
const analyticsData = ref(null)
const analyzing = ref(false)
const analyticsDone = ref(false)
const analyticsStatus = ref('')
const barOption = ref(null)
const scatterOption = ref(null)

async function runAnalysis() {
  analyzing.value = true
  try {
    const r = await datasetAPI.analyze(info.value.root_dir)
    if (r.success) {
      analyticsData.value = r.data; analyticsDone.value = true
      analyticsStatus.value = `✅  ${r.data.total_instances} 框，${r.data.class_count} 类`
      // Update class counts for top bar chart
      if (r.data.bar_data) {
        r.data.bar_data.forEach((d, i) => { classCounts.value[i] = d.count })
      }
      buildCharts(r.data)
    }
  } finally { analyzing.value = false }
}

function buildCharts(data) {
  barOption.value = {
    backgroundColor: 'transparent', textStyle: { color: '#7878a0' },
    grid: { left: 50, right: 16, top: 24, bottom: 60 },
    xAxis: { type: 'category', data: data.bar_data.map(d => d.name),
      axisLabel: { rotate: 25, color: '#7878a0', fontSize: 11 }, axisLine: { lineStyle: { color: '#1e1e35' } } },
    yAxis: { type: 'value', axisLabel: { color: '#7878a0' }, splitLine: { lineStyle: { color: '#1e1e35' } } },
    series: [{ type: 'bar', data: data.bar_data.map(d => d.count),
      itemStyle: { borderRadius: [5,5,0,0] }, colorBy: 'data', color: colors,
      label: { show: true, position: 'top', color: '#c0c0d8', fontSize: 11 } }],
    tooltip: { trigger: 'axis', backgroundColor: '#12121f', borderColor: '#252545' },
  }
  scatterOption.value = {
    backgroundColor: 'transparent', textStyle: { color: '#7878a0' },
    grid: { left: 50, right: 16, top: 24, bottom: 40 },
    xAxis: { name: '宽(归一化)', nameGap: 28, nameLocation: 'middle', axisLabel: { color: '#7878a0' }, splitLine: { lineStyle: { color: '#1e1e35' } } },
    yAxis: { name: '高', axisLabel: { color: '#7878a0' }, splitLine: { lineStyle: { color: '#1e1e35' } } },
    series: [{ type: 'scatter', data: data.scatter_points.map(p => [p.w, p.h, p.class_id]),
      symbolSize: 4, itemStyle: { opacity: 0.6, color: (p) => colors[(p.data?.[2]??0)%colors.length] } }],
    tooltip: { formatter: (p) => `W:${p.data[0].toFixed(3)}<br/>H:${p.data[1].toFixed(3)}` },
  }
}

// ── Split ───────────────────────────────────────────────────
const ratios = reactive({
  train: { label: 'Train 训练集', val: 80, color: '#6366f1' },
  val:   { label: 'Val 验证集',   val: 10, color: '#10b981' },
  test:  { label: 'Test 测试集',  val: 10, color: '#f97316' },
})
const totalRatio = computed(() => ratios.train.val + ratios.val.val + ratios.test.val)
const ratioOk = computed(() => Math.abs(totalRatio.value - 100) < 1)

function clampRatios(changed) {
  const rest = 100 - ratios[changed].val
  const keys = Object.keys(ratios).filter(k => k !== changed)
  const otherSum = keys.reduce((s, k) => s + ratios[k].val, 0)
  if (otherSum > 0) keys.forEach(k => { ratios[k].val = Math.round(ratios[k].val / otherSum * rest) })
}

const splitOutput = ref(''); const splitSeed = ref(42); const splitMove = ref(false)
const splitting = ref(false); const splitPercent = ref(0); const splitStatus = ref(''); const yamlContent = ref('')

function startSplit() {
  if (!ratioOk.value) { ElMessage.warning('比例之和需为 100%'); return }
  splitting.value = true; splitPercent.value = 0; splitStatus.value = '拆分中…'; yamlContent.value = ''
  const output = splitOutput.value || (info.value.root_dir + '/split')
  datasetAPI.split(
    { root_dir: info.value.root_dir, output_dir: output,
      train_ratio: ratios.train.val/100, val_ratio: ratios.val.val/100, test_ratio: ratios.test.val/100,
      seed: splitSeed.value, move: splitMove.value },
    (ev) => { if (ev.type==='progress') splitPercent.value = ev.percent },
    (ev) => {
      splitting.value = false
      const c = ev.counts||{}
      splitStatus.value = `✅  Train ${c.train||0}  Val ${c.val||0}  Test ${c.test||0}`
      yamlContent.value = ev.yaml_content||''
    },
    (err) => { ElMessage.error(err); splitting.value = false }
  )
}
</script>

<style scoped>
/* Custom ratio slider */
.ratio-slider {
  -webkit-appearance: none;
  height: 4px;
  border-radius: 99px;
  background: var(--bg-4);
  outline: none;
  cursor: pointer;
}
.ratio-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--sc);
  cursor: pointer;
  box-shadow: 0 0 8px var(--sc);
  border: 2px solid var(--bg-2);
}
</style>
