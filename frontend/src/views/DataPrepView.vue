<template>
  <div class="page-root">
    <!-- Page Header -->
    <header class="page-header">
      <h1 class="page-title">数据准备</h1>
      <p class="page-sub">视频抽帧 · 图像清洗 · 批量重命名</p>
    </header>

    <!-- ── Bento Grid ──────────────────────────────────── -->
    <div class="flex-1 overflow-y-auto p-6 scroll-y">
      <div class="grid grid-cols-5 gap-4 h-full" style="min-height:540px">

        <!-- ══ LEFT: Big Dropzone / Control Card ═════════ -->
        <div class="col-span-3 flex flex-col gap-4">

          <!-- Video Dropzone -->
          <div
            class="bento-card flex-1 flex flex-col cursor-pointer transition-all duration-200 relative overflow-hidden p-5"
            :class="isDragging ? 'glow-ring border-accent/50' : 'hover:border-border-2'"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="onVideoDrop"
          >
            <!-- Ambient glow when dragging -->
            <div class="absolute inset-0 pointer-events-none transition-opacity duration-300 rounded-[14px]"
              :class="isDragging ? 'opacity-100' : 'opacity-0'"
              style="background:radial-gradient(ellipse at 50% 30%, rgba(99,102,241,0.15) 0%, transparent 70%)">
            </div>

            <div class="flex items-center gap-2 mb-4 relative z-10">
              <div class="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center">
                <Film :size="16" class="text-accent-light" />
              </div>
              <div>
                <div class="text-sm font-semibold text-ink-1">视频抽帧</div>
                <div class="text-[11px] text-ink-3">从视频文件提取关键帧作为训练素材</div>
              </div>
            </div>

            <!-- Drop area -->
            <div class="flex-1 rounded-xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center gap-3 relative"
              :class="isDragging ? 'border-accent/60 bg-accent/5' : 'border-border-2 hover:border-accent/30 hover:bg-accent/3'"
            >
              <div v-if="!videoPath" class="text-center">
                <div class="w-12 h-12 rounded-2xl bg-bg-4 border border-border-2 flex items-center justify-center mx-auto mb-3">
                  <Upload :size="20" class="text-ink-3" />
                </div>
                <div class="text-sm text-ink-2 font-medium">拖拽视频到此处</div>
                <div class="text-xs text-ink-4 mt-1">支持 .mp4 · .avi · .mov · .mkv</div>
              </div>
              <div v-else class="text-center">
                <div class="text-3xl mb-2">🎬</div>
                <div class="text-sm font-semibold text-em-green">{{ videoName }}</div>
              </div>
            </div>

            <!-- Path input -->
            <div class="mt-3 relative z-10">
              <el-input v-model="videoPath" placeholder="或粘贴视频文件完整路径" @change="loadVideoInfo" size="small">
                <template #prefix><span class="text-ink-4 text-xs">PATH</span></template>
              </el-input>
            </div>

            <!-- Video meta cards -->
            <div v-if="videoInfo" class="grid grid-cols-4 gap-2 mt-3 relative z-10">
              <div v-for="m in videoMeta" :key="m.label" class="rounded-lg bg-bg-4 border border-border-1 p-2 text-center">
                <div class="text-sm font-bold text-ink-1">{{ m.val }}</div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mt-0.5">{{ m.label }}</div>
              </div>
            </div>
          </div>

          <!-- Image Clean card -->
          <div class="bento-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-em-orange/10 border border-em-orange/20 flex items-center justify-center">
                <Sparkles :size="16" class="text-em-orange" />
              </div>
              <div>
                <div class="text-sm font-semibold text-ink-1">图像清洗</div>
                <div class="text-[11px] text-ink-3">过滤尺寸过小或文件过小的劣质图片</div>
              </div>
            </div>

            <!-- Clean folder drop -->
            <div
              class="rounded-xl border-2 border-dashed p-3 mb-3 flex items-center gap-2 cursor-pointer transition-all duration-200"
              :class="isCleanDrag ? 'border-em-orange/50 bg-em-orange/5' : 'border-border-2 hover:border-em-orange/30'"
              @dragover.prevent="isCleanDrag = true"
              @dragleave="isCleanDrag = false"
              @drop.prevent="onCleanDrop"
            >
              <FolderOpen :size="14" class="text-ink-4 flex-shrink-0"/>
              <span class="text-xs text-ink-3 truncate">{{ cleanFolder || '拖入图片文件夹' }}</span>
            </div>
            <el-input v-model="cleanFolder" placeholder="图片文件夹路径" size="small" class="mb-3"/>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1">最小宽 (px)</div>
                <el-input-number v-model="minWidth" :min="0" size="small" style="width:100%"/>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1">最小高 (px)</div>
                <el-input-number v-model="minHeight" :min="0" size="small" style="width:100%"/>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1">最小大小 (KB)</div>
                <el-input-number v-model="minSizeKb" :min="0" size="small" style="width:100%"/>
              </div>
            </div>

            <!-- Scan results -->
            <div v-if="scanResults.length" class="mt-3">
              <el-progress v-if="scanning" :percentage="scanPercent" :show-text="false" class="mb-2"/>
              <div class="flex items-center gap-2 justify-between text-xs text-ink-3 mb-2">
                <span>共 <b class="text-ink-1">{{ scanResults.length }}</b> 张</span>
                <span>问题 <b class="text-em-red">{{ badResults.length }}</b> 张</span>
              </div>
              <el-table v-if="badResults.length" :data="badResults" height="160" size="small">
                <el-table-column prop="filename" label="文件名"/>
                <el-table-column prop="size_kb" label="KB" width="65"/>
                <el-table-column prop="reason" label="原因" width="100">
                  <template #default="{row}">
                    <span class="text-em-red text-[11px]">{{ row.reason }}</span>
                  </template>
                </el-table-column>
              </el-table>
              <div v-else-if="!scanning" class="text-center text-em-green text-xs py-2">✅  全部图片完好</div>
            </div>
          </div>
        </div>

        <!-- ══ RIGHT: Control Stack ═══════════════════════ -->
        <div class="col-span-2 flex flex-col gap-4">

          <!-- Extract Config card -->
          <div class="bento-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center">
                <SlidersHorizontal :size="16" class="text-accent-light" />
              </div>
              <div class="text-sm font-semibold text-ink-1">抽帧参数</div>
            </div>

            <div class="space-y-3">
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">抽帧模式</div>
                <el-radio-group v-model="extractMode" size="small" style="width:100%">
                  <el-radio-button label="time" style="flex:1">按时间</el-radio-button>
                  <el-radio-button label="frame" style="flex:1">按帧数</el-radio-button>
                </el-radio-group>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">{{ extractMode === 'time' ? '间隔（秒）' : '每 N 帧' }}</div>
                <el-input-number v-model="extractInterval" :min="0.1" :step="extractMode==='time'?0.5:1" size="small" style="width:100%"/>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">文件前缀</div>
                <el-input v-model="extractPrefix" placeholder="frame" size="small"/>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">输出目录</div>
                <el-input v-model="extractOutput" placeholder="默认：视频目录/frames" size="small"/>
              </div>
            </div>

            <!-- Extract progress -->
            <div v-if="extracting || extractStatus" class="mt-4">
              <el-progress v-if="extracting" :percentage="extractPercent"
                striped striped-flow :duration="5" :show-text="false" class="mb-2"/>
              <div v-if="extractStatus" class="text-xs" :class="extractStatus.startsWith('✅') ? 'text-em-green' : 'text-ink-3'">
                {{ extractStatus }}
              </div>
            </div>
          </div>

          <!-- Batch Rename card -->
          <div class="bento-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-em-purple/10 border border-em-purple/20 flex items-center justify-center">
                <PenLine :size="16" class="text-em-purple" />
              </div>
              <div>
                <div class="text-sm font-semibold text-ink-1">批量重命名</div>
                <div class="text-[11px] text-ink-3">统一格式重命名图片文件名</div>
              </div>
            </div>

            <div class="space-y-3">
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">来源文件夹</div>
                <el-input v-model="renameSource" placeholder="输入路径" size="small"/>
              </div>
              <div>
                <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">输出文件夹（留空=原地）</div>
                <el-input v-model="renameOutput" placeholder="留空原地重命名" size="small"/>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">前缀</div>
                  <el-input v-model="renamePrefix" placeholder="image" size="small"/>
                </div>
                <div>
                  <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-1.5">起始序号</div>
                  <el-input-number v-model="renameStartSeq" :min="-1" size="small" style="width:100%"/>
                </div>
              </div>
            </div>

            <div class="flex gap-2 mt-4">
              <el-button size="small" :disabled="!renameSource" @click="previewRename" class="flex-1">预览</el-button>
              <el-button type="primary" size="small" :disabled="!renameEntries.length" @click="executeRename" class="flex-1">
                执行 ({{ renameEntries.length }})
              </el-button>
            </div>
            <div v-if="renameStatus" class="text-xs text-em-green mt-2">{{ renameStatus }}</div>

            <el-table v-if="renameEntries.length" :data="renameEntries" height="180" size="small" class="mt-3">
              <el-table-column prop="old_name" label="原名"/>
              <el-table-column width="28" align="center"><template #default>→</template></el-table-column>
              <el-table-column prop="new_name" label="新名">
                <template #default="{row}"><span class="text-em-green">{{ row.new_name }}</span></template>
              </el-table-column>
            </el-table>
          </div>

          <!-- Thumbnail strip -->
          <div v-if="thumbs.length" class="bento-card p-4">
            <div class="text-[10px] text-ink-4 uppercase tracking-wider mb-2">最近抽帧预览</div>
            <div class="grid grid-cols-4 gap-1.5">
              <div v-for="(t,i) in thumbs.slice(-8)" :key="i" class="aspect-video rounded overflow-hidden bg-bg-4">
                <img :src="t" class="w-full h-full object-cover hover:scale-110 transition-transform duration-200"/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ Frosted Glass Action Bar ══════════════════════ -->
    <transition name="action-bar">
      <div v-if="canAct" class="action-bar glass border-t border-border-1 px-6 py-3 flex items-center gap-4 flex-shrink-0">
        <!-- Progress summary -->
        <div v-if="extracting || scanning" class="flex items-center gap-3 flex-1">
          <div class="w-full max-w-xs">
            <el-progress :percentage="extracting ? extractPercent : scanPercent" :show-text="false"/>
          </div>
          <span class="text-xs text-ink-3">{{ extracting ? `已保存 ${extractSaved} 帧` : '扫描中…' }}</span>
        </div>
        <div v-else class="flex-1 text-xs text-ink-3">
          {{ actionBarHint }}
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2">
          <el-button
            v-if="videoPath && !extracting"
            type="primary" size="default"
            @click="startExtract"
            :loading="extracting"
          >
            <Play :size="14" class="mr-1.5"/> 开始抽帧
          </el-button>
          <el-button
            v-if="cleanFolder && !scanning"
            size="default"
            @click="startScan"
            :loading="scanning"
            style="border-color:var(--em-orange,#f97316);color:#f97316"
          >
            <Search :size="14" class="mr-1.5"/> 扫描清洗
          </el-button>
          <el-button
            v-if="badResults.length && !scanning"
            type="danger" size="default"
            @click="deleteBad"
          >
            <Trash2 :size="14" class="mr-1.5"/> 删除 {{ badResults.length }} 个
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { dataPrepAPI } from '../api'
import {
  Film, Upload, Sparkles, SlidersHorizontal, PenLine,
  FolderOpen, Play, Search, Trash2
} from 'lucide-vue-next'

// ── Video Extract ────────────────────────────────────────
const videoPath = ref('')
const videoName = ref('')
const videoInfo = ref(null)
const extractMode = ref('time')
const extractInterval = ref(1)
const extractPrefix = ref('frame')
const extractOutput = ref('')
const extracting = ref(false)
const extractPercent = ref(0)
const extractSaved = ref(0)
const extractStatus = ref('')
const thumbs = ref([])
const isDragging = ref(false)

const videoMeta = computed(() => videoInfo.value ? [
  { label: 'FPS',  val: videoInfo.value.fps },
  { label: '帧数',  val: videoInfo.value.total_frames?.toLocaleString() },
  { label: '分辨率', val: `${videoInfo.value.width}×${videoInfo.value.height}` },
  { label: '时长',  val: `${videoInfo.value.duration_sec}s` },
] : [])

async function loadVideoInfo() {
  if (!videoPath.value) return
  videoName.value = videoPath.value.split(/[\\/]/).pop()
  try {
    const r = await dataPrepAPI.getVideoInfo(videoPath.value)
    if (r.success) videoInfo.value = r.data
  } catch {}
}

function onVideoDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) { videoPath.value = f.path || f.name; loadVideoInfo() }
}

function startExtract() {
  extracting.value = true; extractPercent.value = 0; extractSaved.value = 0
  extractStatus.value = ''; thumbs.value = []
  const output = extractOutput.value || (videoPath.value.replace(/[^\\/]+$/, '') + 'frames')
  dataPrepAPI.extractFrames(
    { video_path: videoPath.value, output_dir: output, mode: extractMode.value, interval: extractInterval.value, prefix: extractPrefix.value },
    (ev) => {
      if (ev.type === 'progress') {
        extractPercent.value = ev.percent; extractSaved.value = ev.saved
        if (ev.thumb_path) thumbs.value.push(`http://127.0.0.1:8765/api/dataset/image?path=${encodeURIComponent(ev.thumb_path)}`)
      }
    },
    (ev) => { extractStatus.value = `✅  完成！已保存 ${ev?.saved} 帧`; extracting.value = false },
    (err) => { extractStatus.value = `❌  ${err}`; extracting.value = false }
  )
}

// ── Image Clean ──────────────────────────────────────────
const cleanFolder = ref('')
const minWidth = ref(0); const minHeight = ref(0); const minSizeKb = ref(0)
const scanning = ref(false); const scanPercent = ref(0)
const scanResults = ref([]); const isCleanDrag = ref(false)
const badResults = computed(() => scanResults.value.filter(r => r.should_remove))

function onCleanDrop(e) {
  isCleanDrag.value = false
  const f = e.dataTransfer.files[0]
  if (f) cleanFolder.value = f.path || f.name
}

function startScan() {
  scanning.value = true; scanPercent.value = 0; scanResults.value = []
  dataPrepAPI.scanImages(
    { folder_path: cleanFolder.value, min_width: minWidth.value, min_height: minHeight.value, min_size_kb: minSizeKb.value },
    (ev) => { if (ev.type === 'progress') scanPercent.value = ev.percent },
    (ev) => { scanResults.value = ev.results || []; scanning.value = false },
    (err) => { ElMessage.error(err); scanning.value = false }
  )
}

async function deleteBad() {
  const r = await dataPrepAPI.deleteImages(badResults.value.map(r => r.path))
  if (r.success) { ElMessage.success(`已删除 ${r.data.success} 个`); startScan() }
}

// ── Batch Rename ─────────────────────────────────────────
const renameSource = ref(''); const renameOutput = ref('')
const renamePrefix = ref('image'); const renameStartSeq = ref(-1)
const renameEntries = ref([]); const renameStatus = ref('')

async function previewRename() {
  const r = await dataPrepAPI.renamePreview({
    source_folder: renameSource.value,
    output_folder: renameOutput.value || renameSource.value,
    prefix: renamePrefix.value,
    start_seq: renameStartSeq.value
  })
  if (r.success) renameEntries.value = r.data
}
async function executeRename() {
  const r = await dataPrepAPI.renameExecute(renameEntries.value)
  if (r.success) { renameStatus.value = `✅  成功 ${r.data.success} 个`; renameEntries.value = [] }
}

// ── Action Bar ───────────────────────────────────────────
const canAct = computed(() => videoPath.value || cleanFolder.value || extracting.value || scanning.value || badResults.value.length)
const actionBarHint = computed(() => {
  if (videoPath.value && !cleanFolder.value) return '已选视频，点击「开始抽帧」提取训练帧'
  if (cleanFolder.value && !videoPath.value) return '已选文件夹，点击「扫描清洗」检测劣质图片'
  return '配置参数后点击右侧按钮执行任务'
})
</script>

<style scoped>
.action-bar-enter-active, .action-bar-leave-active { transition: all 0.25s ease; }
.action-bar-enter-from, .action-bar-leave-to { opacity: 0; transform: translateY(100%); }
</style>
