<template>
  <div class="page-root">
    <!-- ── 页头 ─────────────────────────────────────────── -->
    <div class="page-header">
      <h1 class="page-title flex items-center gap-2">
        <Download :size="20" class="text-accent" />
        模型导出
        <span class="text-xs font-normal text-ink-3 ml-1">Model Export · ONNX</span>
      </h1>
      <p class="page-sub">将训练好的 .pt 权重文件转化为 ONNX 格式，支持 Opset 版本选择与 FP16 半精度量化</p>
    </div>

    <!-- ── 主体两栏 ────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden gap-0 mt-4">

      <!-- ① 左侧控制面板 320px -->
      <aside class="w-[320px] flex-shrink-0 flex flex-col gap-3 px-4 pb-4 overflow-y-auto scroll-y border-r border-border-1">

        <!-- ── 权重扫描 ─────────────────────────────── -->
        <div class="bento-card p-3">
          <div class="section-label">📂 源模型选择</div>

          <!-- 项目路径输入 -->
          <div class="flex gap-2 mt-2">
            <input
              v-model="projectDir"
              class="input-field flex-1 text-xs"
              placeholder="输入项目根目录路径..."
              @keyup.enter="scanWeights"
            />
            <button
              class="btn-icon"
              title="浏览文件夹"
              @click="browseDir"
            >
              <FolderOpen :size="14" />
            </button>
          </div>

          <!-- 扫描按钮 -->
          <button
            class="btn-secondary w-full mt-2 gap-1.5"
            :disabled="!projectDir || scanning"
            @click="scanWeights"
          >
            <Loader2 v-if="scanning" :size="13" class="animate-spin" />
            <Search v-else :size="13" />
            {{ scanning ? '扫描中...' : '扫描权重文件' }}
          </button>

          <!-- 权重列表下拉 -->
          <div v-if="weightList.length" class="mt-2">
            <div class="text-[10px] text-ink-4 font-semibold uppercase tracking-wider mb-1">
              找到 {{ weightList.length }} 个权重文件
            </div>
            <select
              v-model="selectedWeight"
              class="input-field w-full text-xs"
            >
              <option value="" disabled>— 请选择权重文件 —</option>
              <option
                v-for="w in weightList"
                :key="w.path"
                :value="w.path"
              >{{ w.relative }} ({{ w.size_mb }} MB)</option>
            </select>
          </div>

          <!-- 选中文件信息 -->
          <div v-if="selectedWeightInfo" class="mt-2 p-2 rounded-lg bg-bg-3 border border-border-1">
            <div class="flex items-center gap-1.5 text-xs">
              <FileText :size="12" class="text-accent flex-shrink-0" />
              <span class="text-ink-2 font-mono truncate">{{ selectedWeightInfo.name }}</span>
            </div>
            <div class="flex gap-3 mt-1.5">
              <span class="text-[10px] text-ink-4">大小：<span class="text-ink-3">{{ selectedWeightInfo.size_mb }} MB</span></span>
              <span v-if="selectedWeightInfo.is_priority" class="text-[10px] text-em-green font-semibold">● runs/train</span>
            </div>
          </div>
        </div>

        <!-- ── 导出配置 ─────────────────────────────── -->
        <div class="bento-card p-3">
          <div class="section-label">⚙️ 导出配置</div>

          <!-- 目标格式选择（按钮组） -->
          <div class="mt-2">
            <div class="text-[10px] text-ink-4 mb-1.5">目标格式</div>
            <div class="flex gap-2">
              <button
                class="format-btn format-active flex-1"
                title="ONNX 格式（当前仅支持）"
              >
                <span class="font-bold">ONNX</span>
                <span class="text-[9px] opacity-70">.onnx</span>
              </button>
              <button class="format-btn format-disabled flex-1" disabled title="即将支持">
                <span class="font-bold">TRT</span>
                <span class="text-[9px] opacity-50">Coming Soon</span>
              </button>
              <button class="format-btn format-disabled flex-1" disabled title="即将支持">
                <span class="font-bold">CoreML</span>
                <span class="text-[9px] opacity-50">Coming Soon</span>
              </button>
            </div>
          </div>

          <!-- Opset Version -->
          <div class="mt-3">
            <div class="flex items-center justify-between mb-1.5">
              <div class="text-[10px] text-ink-4">Opset Version</div>
              <span class="text-[10px] text-accent-light font-mono font-bold">{{ config.opset }}</span>
            </div>
            <div class="flex gap-1.5">
              <button
                v-for="v in [11, 12, 13, 14, 17]"
                :key="v"
                class="opset-btn flex-1"
                :class="config.opset === v ? 'opset-active' : 'opset-idle'"
                @click="config.opset = v"
              >{{ v }}</button>
            </div>
          </div>

          <!-- 图像尺寸 -->
          <div class="mt-3">
            <div class="flex items-center justify-between mb-1.5">
              <div class="text-[10px] text-ink-4">图像尺寸 (imgsz)</div>
              <span class="text-[10px] text-ink-3 font-mono">{{ config.imgsz }}×{{ config.imgsz }}</span>
            </div>
            <div class="flex gap-2 items-center">
              <input
                v-model.number="config.imgsz"
                type="number"
                step="32"
                min="32"
                max="1920"
                class="input-field w-24 text-xs text-center font-mono"
              />
              <div class="flex gap-1 flex-1">
                <button
                  v-for="sz in [320, 416, 640, 1280]"
                  :key="sz"
                  class="opset-btn flex-1 text-[9px]"
                  :class="config.imgsz === sz ? 'opset-active' : 'opset-idle'"
                  @click="config.imgsz = sz"
                >{{ sz }}</button>
              </div>
            </div>
          </div>

          <!-- FP16 Half 量化 -->
          <div class="mt-3 flex items-start justify-between gap-3">
            <div>
              <div class="text-[11px] text-ink-2 font-semibold flex items-center gap-1">
                <Zap :size="12" class="text-em-amber" />
                FP16 半精度 (Half)
              </div>
              <div class="text-[10px] text-ink-4 mt-0.5">模型体积减半，需 GPU/专用硬件推理</div>
            </div>
            <button
              class="toggle-switch flex-shrink-0 mt-0.5"
              :class="config.half ? 'toggle-on' : 'toggle-off'"
              @click="config.half = !config.half"
              role="switch"
              :aria-checked="config.half"
            >
              <span class="toggle-thumb" :class="config.half ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <!-- Simplify -->
          <div class="mt-2 flex items-start justify-between gap-3">
            <div>
              <div class="text-[11px] text-ink-2 font-semibold flex items-center gap-1">
                <Sparkles :size="12" class="text-em-purple" />
                onnxsim 图优化 (Simplify)
              </div>
              <div class="text-[10px] text-ink-4 mt-0.5">精简计算图，提升推理速度（需安装 onnxsim）</div>
            </div>
            <button
              class="toggle-switch flex-shrink-0 mt-0.5"
              :class="config.simplify ? 'toggle-on' : 'toggle-off'"
              @click="config.simplify = !config.simplify"
              role="switch"
              :aria-checked="config.simplify"
            >
              <span class="toggle-thumb" :class="config.simplify ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <!-- 输出目录 -->
          <div class="mt-3">
            <div class="text-[10px] text-ink-4 mb-1.5">输出目录</div>
            <div class="flex gap-2">
              <input
                v-model="config.output_dir"
                class="input-field flex-1 text-xs"
                placeholder="默认与源模型同目录"
              />
              <button class="btn-icon" @click="browseOutputDir" title="浏览">
                <FolderOpen :size="14" />
              </button>
            </div>
          </div>
        </div>

        <!-- ── 导出按钮 ─────────────────────────────── -->
        <button
          class="export-btn"
          :class="canExport ? 'export-btn-active' : 'export-btn-disabled'"
          :disabled="!canExport || exporting"
          @click="startExport"
        >
          <div v-if="exporting" class="flex items-center gap-2 justify-center">
            <Loader2 :size="16" class="animate-spin" />
            <span>导出中...</span>
          </div>
          <div v-else class="flex items-center gap-2 justify-center">
            <Download :size="16" />
            <span>开始导出 ONNX</span>
          </div>
        </button>

      </aside>

      <!-- ② 右侧日志/结果区 flex-1 -->
      <main class="flex-1 flex flex-col overflow-hidden bg-bg-1 p-4">

        <!-- 空态：未开始 -->
        <div
          v-if="status === 'idle'"
          class="flex-1 flex flex-col items-center justify-center text-center gap-4"
        >
          <div class="w-20 h-20 rounded-2xl flex items-center justify-center"
            style="background:linear-gradient(135deg,rgba(99,102,241,.15),rgba(139,92,246,.1));border:1px solid rgba(99,102,241,.2)">
            <Download :size="36" class="text-accent/60" />
          </div>
          <div>
            <div class="text-sm font-semibold text-ink-3 mb-1">等待导出任务</div>
            <div class="text-xs text-ink-4 max-w-xs">
              在左侧选择 .pt 权重文件，配置导出参数，<br>然后点击「开始导出 ONNX」
            </div>
          </div>
          <!-- 快速说明 -->
          <div class="grid grid-cols-3 gap-3 mt-2 max-w-sm">
            <div class="p-2.5 rounded-xl bg-bg-2 border border-border-1 text-center">
              <div class="text-base mb-1">🔍</div>
              <div class="text-[10px] text-ink-4">扫描权重</div>
            </div>
            <div class="p-2.5 rounded-xl bg-bg-2 border border-border-1 text-center">
              <div class="text-base mb-1">⚙️</div>
              <div class="text-[10px] text-ink-4">配置参数</div>
            </div>
            <div class="p-2.5 rounded-xl bg-bg-2 border border-border-1 text-center">
              <div class="text-base mb-1">🚀</div>
              <div class="text-[10px] text-ink-4">一键导出</div>
            </div>
          </div>
        </div>

        <!-- 导出中：实时日志窗 -->
        <div v-else-if="status === 'exporting'" class="flex-1 flex flex-col gap-3">
          <!-- 进度提示 -->
          <div class="flex items-center gap-2 p-3 rounded-xl bg-bg-2 border border-accent/20">
            <Loader2 :size="14" class="text-accent animate-spin flex-shrink-0" />
            <span class="text-xs text-ink-2 font-medium">正在导出：<span class="text-accent-light font-mono">{{ exportingFileName }}</span></span>
          </div>

          <!-- 日志终端 -->
          <div
            ref="logPanelRef"
            class="flex-1 rounded-xl bg-[#0d1117] border border-border-1 p-3 overflow-y-auto font-mono text-[11px] leading-relaxed"
            style="min-height:0"
          >
            <div
              v-for="(line, i) in logLines"
              :key="i"
              class="log-line"
              :class="getLogClass(line)"
            >
              <span class="text-ink-4 select-none mr-2">›</span>{{ line }}
            </div>
            <!-- 光标闪烁 -->
            <span class="inline-block w-1.5 h-3 bg-accent/70 animate-pulse ml-1 align-middle" />
          </div>
        </div>

        <!-- 导出完成：结果卡片 -->
        <div v-else-if="status === 'done'" class="flex-1 flex flex-col gap-4">
          <!-- 成功横幅 -->
          <div class="flex items-center gap-3 p-4 rounded-xl bg-em-green/10 border border-em-green/25">
            <div class="w-9 h-9 rounded-full bg-em-green/15 border border-em-green/30 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 :size="18" class="text-em-green" />
            </div>
            <div>
              <div class="text-sm font-bold text-em-green">🎉 导出成功！</div>
              <div class="text-xs text-ink-3 mt-0.5">{{ exportResult.message }}</div>
            </div>
            <div class="ml-auto text-right">
              <div class="text-xs text-ink-4">耗时</div>
              <div class="text-sm font-mono font-bold text-ink-2">{{ exportElapsedSec }}s</div>
            </div>
          </div>

          <!-- 文件详情卡 -->
          <div class="bento-card p-4">
            <div class="section-label mb-3">📄 输出文件信息</div>
            <div class="space-y-2">
              <div class="detail-row">
                <span class="detail-label">文件路径</span>
                <span class="detail-value font-mono text-[10px] break-all">{{ exportResult.output_path }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">文件大小</span>
                <span class="detail-value font-semibold text-em-green">{{ exportResult.size_mb }} MB</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Opset</span>
                <span class="detail-value font-mono">{{ config.opset }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">图像尺寸</span>
                <span class="detail-value font-mono">{{ config.imgsz }}×{{ config.imgsz }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">FP16 量化</span>
                <span class="detail-value">
                  <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                    :class="config.half ? 'bg-em-amber/15 text-em-amber border border-em-amber/30' : 'bg-bg-4 text-ink-4 border border-border-1'">
                    {{ config.half ? '✓ 已开启' : '— 未启用' }}
                  </span>
                </span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Simplify</span>
                <span class="detail-value">
                  <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                    :class="config.simplify ? 'bg-em-purple/15 text-em-purple border border-em-purple/30' : 'bg-bg-4 text-ink-4 border border-border-1'">
                    {{ config.simplify ? '✓ 已优化' : '— 未优化' }}
                  </span>
                </span>
              </div>
            </div>
          </div>

          <!-- 操作按钮区 -->
          <div class="flex gap-2">
            <button class="btn-primary flex-1 gap-2" @click="openOutputDir">
              <FolderOpen :size="14" />
              打开所在目录
            </button>
            <button class="btn-secondary flex-1 gap-2" @click="resetExport">
              <RotateCcw :size="14" />
              重新导出
            </button>
          </div>

          <!-- 折叠日志 -->
          <details class="group">
            <summary class="cursor-pointer text-xs text-ink-4 hover:text-ink-3 flex items-center gap-1 select-none">
              <ChevronDown :size="12" class="transition-transform group-open:rotate-180" />
              查看完整日志（{{ logLines.length }} 行）
            </summary>
            <div class="mt-2 rounded-xl bg-[#0d1117] border border-border-1 p-3 overflow-y-auto font-mono text-[11px] leading-relaxed max-h-60">
              <div v-for="(line, i) in logLines" :key="i" class="log-line" :class="getLogClass(line)">
                <span class="text-ink-4 select-none mr-2">›</span>{{ line }}
              </div>
            </div>
          </details>
        </div>

        <!-- 导出失败 -->
        <div v-else-if="status === 'error'" class="flex-1 flex flex-col gap-4">
          <!-- 错误横幅 -->
          <div class="flex items-start gap-3 p-4 rounded-xl bg-em-red/10 border border-em-red/25">
            <div class="w-9 h-9 rounded-full bg-em-red/15 border border-em-red/30 flex items-center justify-center flex-shrink-0 mt-0.5">
              <XCircle :size="18" class="text-em-red" />
            </div>
            <div class="flex-1">
              <div class="text-sm font-bold text-em-red mb-1">导出失败</div>
              <div class="text-xs text-ink-3 font-mono break-all">{{ exportError }}</div>
            </div>
          </div>

          <!-- 错误日志 -->
          <div class="flex-1 rounded-xl bg-[#0d1117] border border-border-1 p-3 overflow-y-auto font-mono text-[11px] leading-relaxed" style="min-height:0">
            <div v-for="(line, i) in logLines" :key="i" class="log-line" :class="getLogClass(line)">
              <span class="text-ink-4 select-none mr-2">›</span>{{ line }}
            </div>
          </div>

          <button class="btn-secondary w-full gap-2" @click="resetExport">
            <RotateCcw :size="14" />
            重试 / 重新配置
          </button>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download, FolderOpen, Search, Loader2, FileText,
  Zap, Sparkles, CheckCircle2, XCircle, RotateCcw,
  ChevronDown
} from 'lucide-vue-next'
import { exportAPI } from '../api/index'

// ── 状态 ─────────────────────────────────────────────────
const projectDir = ref('')
const scanning = ref(false)
const weightList = ref([])
const selectedWeight = ref('')

const config = ref({
  opset: 12,
  imgsz: 640,
  half: false,
  simplify: true,
  output_dir: '',
})

// 导出状态：idle | exporting | done | error
const status = ref('idle')
const logLines = ref([])
const logPanelRef = ref(null)
const exporting = ref(false)
const exportingFileName = ref('')
const exportResult = ref(null)
const exportError = ref('')
const exportStartTime = ref(0)
const exportElapsedSec = ref(0)

// ── 计算属性 ─────────────────────────────────────────────
const selectedWeightInfo = computed(() =>
  weightList.value.find(w => w.path === selectedWeight.value) ?? null
)

const canExport = computed(() =>
  !!selectedWeight.value && !exporting.value
)

// 当选中权重变更时，自动填充输出目录
watch(selectedWeight, (path) => {
  if (!config.value.output_dir && path) {
    // 默认输出到与权重同级的 export 目录
    const lastSep = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
    config.value.output_dir = path.substring(0, lastSep)
  }
})

// ── Tauri 文件对话框 ──────────────────────────────────────
async function browseDir() {
  try {
    if (window.__TAURI__) {
      const { open } = await import('@tauri-apps/api/dialog')
      const dir = await open({ directory: true, title: '选择项目根目录' })
      if (dir) projectDir.value = dir
    }
  } catch (e) {
    ElMessage.warning('请手动输入项目目录路径')
  }
}

async function browseOutputDir() {
  try {
    if (window.__TAURI__) {
      const { open } = await import('@tauri-apps/api/dialog')
      const dir = await open({ directory: true, title: '选择输出目录' })
      if (dir) config.value.output_dir = dir
    }
  } catch (e) {
    ElMessage.warning('请手动输入输出目录路径')
  }
}

async function openOutputDir() {
  try {
    if (window.__TAURI__ && exportResult.value?.output_path) {
      const { open } = await import('@tauri-apps/api/shell')
      // 打开文件所在目录
      const path = exportResult.value.output_path
      const dir = path.substring(0, Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')))
      await open(dir)
    } else {
      ElMessage.info(`输出路径：${exportResult.value?.output_path}`)
    }
  } catch (e) {
    ElMessage.error('无法打开目录：' + e)
  }
}

// ── 扫描权重 ─────────────────────────────────────────────
async function scanWeights() {
  if (!projectDir.value) return
  scanning.value = true
  weightList.value = []
  selectedWeight.value = ''
  try {
    const res = await exportAPI.scanWeights(projectDir.value)
    if (res.error) {
      ElMessage.error(res.error)
      return
    }
    weightList.value = res.weights
    if (res.weights.length === 0) {
      ElMessage.warning('未找到任何 .pt 权重文件，请确认目录正确')
    } else {
      // 自动选中第一个优先权重（best.pt）
      const first = res.weights[0]
      selectedWeight.value = first.path
      ElMessage.success(`找到 ${res.weights.length} 个权重文件`)
    }
  } catch (e) {
    ElMessage.error(`扫描失败：${e}`)
  } finally {
    scanning.value = false
  }
}

// ── 滚动日志到底部 ────────────────────────────────────────
function scrollLogToBottom() {
  nextTick(() => {
    if (logPanelRef.value) {
      logPanelRef.value.scrollTop = logPanelRef.value.scrollHeight
    }
  })
}

// ── 日志行样式 ────────────────────────────────────────────
function getLogClass(line) {
  const l = line.toLowerCase()
  if (l.includes('error') || l.includes('failed') || l.includes('traceback'))
    return 'text-em-red/90'
  if (l.includes('warning') || l.includes('warn'))
    return 'text-em-amber/90'
  if (l.includes('success') || l.includes('done') || l.includes('完成') || l.includes('saved'))
    return 'text-em-green/90'
  if (l.includes('onnx') || l.includes('export'))
    return 'text-accent-light/90'
  return 'text-ink-3/80'
}

// ── 开始导出 ─────────────────────────────────────────────
function startExport() {
  if (!canExport.value) return

  // 重置状态
  logLines.value = []
  exportResult.value = null
  exportError.value = ''
  status.value = 'exporting'
  exporting.value = true
  exportStartTime.value = Date.now()
  exportingFileName.value = selectedWeightInfo.value?.name ?? ''

  const params = {
    model_path: selectedWeight.value,
    output_dir: config.value.output_dir || projectDir.value,
    opset: config.value.opset,
    imgsz: config.value.imgsz,
    half: config.value.half,
    simplify: config.value.simplify,
  }

  exportAPI.exportModel(
    params,
    // onEvent: 每条 SSE 事件
    (event) => {
      if (event.type === 'log' || event.type === 'start') {
        logLines.value.push(event.message)
        scrollLogToBottom()
      }
    },
    // onDone
    (event) => {
      exporting.value = false
      exportElapsedSec.value = ((Date.now() - exportStartTime.value) / 1000).toFixed(1)
      if (event && event.output_path) {
        exportResult.value = event
        status.value = 'done'
        ElMessage.success('ONNX 导出完成！')
      } else {
        // done 事件由 SSE 内部 error 提前触发，此处兜底
        if (status.value !== 'error') {
          status.value = 'done'
        }
      }
    },
    // onError
    (err) => {
      exporting.value = false
      exportError.value = err
      status.value = 'error'
      ElMessage.error(`导出失败：${err}`)
    }
  )
}

// ── 重置 ─────────────────────────────────────────────────
function resetExport() {
  status.value = 'idle'
  logLines.value = []
  exportResult.value = null
  exportError.value = ''
  exporting.value = false
}
</script>

<style scoped>
/* ── 通用 ─────────────────────────────────────────────── */
.section-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-4);
}

/* ── 格式选择按钮 ────────────────────────────────────── */
.format-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 7px 6px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
  gap: 2px;
}
.format-active {
  background: rgba(99,102,241,0.15);
  color: var(--accent-light);
  border-color: rgba(99,102,241,0.4);
}
.format-disabled {
  background: var(--bg-3);
  color: var(--text-4);
  border-color: var(--border-1);
  cursor: not-allowed;
  opacity: 0.6;
}

/* ── Opset 按钮 ──────────────────────────────────────── */
.opset-btn {
  padding: 5px 4px;
  border-radius: 6px;
  border: 1px solid transparent;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.12s;
  text-align: center;
}
.opset-idle {
  background: var(--bg-4);
  color: var(--text-3);
  border-color: var(--border-1);
}
.opset-idle:hover { color: var(--text-2); border-color: var(--border-2); }
.opset-active {
  background: rgba(99,102,241,0.18);
  color: var(--accent-light);
  border-color: rgba(99,102,241,0.45);
}

/* ── Toggle 开关 ─────────────────────────────────────── */
.toggle-switch {
  width: 36px;
  height: 20px;
  border-radius: 999px;
  padding: 2px;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}
.toggle-on  { background: rgba(99,102,241,0.75); }
.toggle-off { background: var(--bg-4); border: 1px solid var(--border-2); }
.toggle-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

/* ── 导出大按钮 ──────────────────────────────────────── */
.export-btn {
  width: 100%;
  padding: 13px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 2px;
}
.export-btn-active {
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  color: white;
  box-shadow: 0 4px 20px rgba(99,102,241,0.35);
}
.export-btn-active:hover {
  box-shadow: 0 6px 28px rgba(99,102,241,0.5);
  transform: translateY(-1px);
}
.export-btn-active:active { transform: translateY(0); }
.export-btn-disabled {
  background: var(--bg-4);
  color: var(--text-4);
  cursor: not-allowed;
}

/* ── 详情行 ──────────────────────────────────────────── */
.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--border-1);
  font-size: 11px;
}
.detail-row:last-child { border-bottom: none; }
.detail-label { color: var(--text-4); flex-shrink: 0; }
.detail-value { color: var(--text-2); text-align: right; }

/* ── 日志行 ──────────────────────────────────────────── */
.log-line {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

/* ── Btn 图标 ────────────────────────────────────────── */
.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--bg-4);
  border: 1px solid var(--border-2);
  color: var(--text-3);
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.btn-icon:hover { color: var(--text-1); border-color: var(--accent-border); }
</style>
