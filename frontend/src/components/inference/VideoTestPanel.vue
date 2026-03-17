<template>
  <div class="flex flex-col h-full overflow-hidden">

    <!-- 空白/未加载提示 -->
    <div v-if="!modelLoaded" class="flex-1 flex flex-col items-center justify-center text-ink-4 gap-3">
      <Video :size="48" class="opacity-20" />
      <span class="text-sm">请先在左侧加载模型</span>
    </div>

    <template v-else>
      <!-- 工具栏 -->
      <div class="flex items-center gap-3 px-5 py-2.5 border-b border-border-1 flex-shrink-0">
        <!-- 导入视频 -->
        <button class="tool-btn" @click="triggerPicker">
          <FolderOpen :size="13" /> 导入视频
        </button>
        <input ref="pickerRef" type="file" accept="video/mp4,video/*" class="hidden" @change="onFileChange" />

        <span v-if="videoName" class="text-xs text-ink-3 truncate flex-1 font-mono">{{ videoName }}</span>
        <div v-else class="flex-1" />

        <!-- FPS 指示器 -->
        <span v-if="playing" class="fps-badge">{{ fps }} FPS</span>

        <!-- 检测框数 -->
        <span v-if="detCount > 0" class="stat-badge">{{ detCount }} 框</span>

        <!-- 推理开关 -->
        <label class="flex items-center gap-1.5 text-xs text-ink-3 cursor-pointer">
          <input type="checkbox" v-model="inferEnabled" class="accent-indigo-500" />
          实时推理
        </label>

        <!-- 录制 / 停止录制 -->
        <button
          v-if="!recording"
          class="tool-btn tool-btn--record"
          :disabled="!playing"
          @click="startRecording"
        >
          <Circle :size="12" class="fill-red-400 text-red-400" /> 录制结果
        </button>
        <button v-else class="tool-btn tool-btn--stop" @click="stopRecording">
          <Square :size="12" /> 停止录制
        </button>
      </div>

      <!-- 视频 + Canvas 叠加 -->
      <div class="flex-1 relative overflow-hidden flex items-center justify-center bg-[#0a0a10]">

        <!-- 无视频时的拖放提示 -->
        <div
          v-if="!videoSrc"
          class="drop-zone absolute inset-8 flex flex-col items-center justify-center border-2 border-dashed border-border-2 rounded-2xl cursor-pointer"
          :class="{ 'border-accent': isDragOver }"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
          @drop.prevent="onDrop"
          @click="triggerPicker"
        >
          <Video :size="36" class="text-ink-4 mb-3 opacity-50" />
          <span class="text-sm text-ink-4 text-center">拖入 .mp4 视频文件，或点击选择</span>
        </div>

        <!-- 视频元素（仅解码用，隐藏） -->
        <video
          ref="videoRef"
          :src="videoSrc"
          class="hidden"
          @loadedmetadata="onVideoReady"
          @ended="onVideoEnded"
          crossorigin="anonymous"
          preload="auto"
        />

        <!-- 渲染 Canvas（显示原帧 + 检测框） -->
        <canvas
          ref="displayCanvasRef"
          class="max-w-full max-h-full object-contain"
          style="image-rendering: crisp-edges;"
        />

        <!-- 控制栏叠加 -->
        <div
          v-if="videoSrc"
          class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2 rounded-xl glass"
        >
          <button class="ctrl-btn" @click="togglePlay">
            <Pause v-if="playing" :size="16" />
            <Play v-else :size="16" />
          </button>
          <!-- 进度条 -->
          <input
            type="range" class="progress-bar"
            min="0" :max="duration" step="0.01"
            :value="currentTime"
            @input="seek"
          />
          <span class="text-xs font-mono text-ink-3 w-20 text-right">
            {{ fmtTime(currentTime) }} / {{ fmtTime(duration) }}
          </span>
        </div>
      </div>

      <!-- 检测结果列表（视频 canvas 下方） -->
      <DetectionList
        :boxes="displayBoxes"
        :infer-ms="lastInferMs"
      />

    </template>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted, computed } from 'vue'
import { Video, FolderOpen, Play, Pause, Circle, Square } from 'lucide-vue-next'
import { inferImage } from '../../api/inference'
import DetectionList from './DetectionList.vue'

const props = defineProps({
  modelLoaded: Boolean,
  conf: { type: Number, default: 0.25 },
  iou: { type: Number, default: 0.45 },
})

// ── 视频源 ─────────────────────────────────────────────
const videoRef = ref(null)
const displayCanvasRef = ref(null)
const pickerRef = ref(null)
const videoSrc = ref(null)
const videoName = ref('')
const isDragOver = ref(false)

// ── 播放状态 ─────────────────────────────────────────
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const fps = ref(0)
const detCount = ref(0)
const inferEnabled = ref(true)

// ── 录制 ─────────────────────────────────────────────
const recording = ref(false)
let mediaRecorder = null
let recordedChunks = []

// ── 推理循环 ─────────────────────────────────────────
let animFrame = null
let lastInferTime = 0
const INFER_INTERVAL_MS = 100   // 每 100ms 推理一次，约 10fps
let fpsCounter = 0
let fpsTimer = 0
const lastInferMs = ref(null)    // 最近一次推理耗时（传给 DetectionList）

const PALETTE = [
  '#6366f1','#10b981','#f97316','#3b82f6','#8b5cf6',
  '#ec4899','#14b8a6','#fbbf24','#ef4444','#06b6d4',
]
function getColor(cls) { return PALETTE[cls % PALETTE.length] }

// 当前检测结果缓存（响应式，供 DetectionList 使用）
const currentBoxesRef = ref([])
let currentBoxes = []           // 内部绘图用（避免每帧触发响应式）

// 过滤后的框（用于 DetectionList 显示，与 conf 同步）
const displayBoxes = computed(() =>
  currentBoxesRef.value.filter(b => b.conf >= props.conf)
)

function triggerPicker() { pickerRef.value?.click() }

function onDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) loadVideoFile(file)
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) loadVideoFile(file)
  e.target.value = ''
}

function loadVideoFile(file) {
  stopLoop()
  if (videoSrc.value) URL.revokeObjectURL(videoSrc.value)
  videoSrc.value = URL.createObjectURL(file)
  videoName.value = file.name
  playing.value = false
  currentBoxes = []
  detCount.value = 0
}

function onVideoReady() {
  duration.value = videoRef.value?.duration || 0
  const video = videoRef.value
  const canvas = displayCanvasRef.value
  if (video && canvas) {
    // 只在这里设一次 canvas 尺寸，后续每帧不再重置（重置会清空 context）
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
  }
  drawFrame()
}

function onVideoEnded() {
  playing.value = false
  stopLoop()
}

async function togglePlay() {
  const video = videoRef.value
  if (!video) return
  if (playing.value) {
    video.pause()
    playing.value = false
    stopLoop()
  } else {
    await video.play()
    playing.value = true
    startLoop()
  }
}

function seek(e) {
  const video = videoRef.value
  if (!video) return
  video.currentTime = +e.target.value
  drawFrame()
}

function startLoop() {
  fpsTimer = Date.now()
  fpsCounter = 0

  function loop() {
    const video = videoRef.value
    if (!video || !playing.value) return
    currentTime.value = video.currentTime

    drawFrame()

    // FPS 计数
    fpsCounter++
    const now = Date.now()
    if (now - fpsTimer >= 1000) {
      fps.value = fpsCounter
      fpsCounter = 0
      fpsTimer = now
    }

    // 推理：限流
    if (inferEnabled.value && props.modelLoaded && now - lastInferTime > INFER_INTERVAL_MS) {
      lastInferTime = now
      captureAndInfer()
    }

    animFrame = requestAnimationFrame(loop)
  }
  animFrame = requestAnimationFrame(loop)
}

function stopLoop() {
  if (animFrame) {
    cancelAnimationFrame(animFrame)
    animFrame = null
  }
  playing.value = false
  fps.value = 0
}

// 将 video 当前帧绘制到 canvas，并叠加检测框
function drawFrame() {
  const video = videoRef.value
  const canvas = displayCanvasRef.value
  if (!video || !canvas || !video.videoWidth) return

  // 仅当 canvas 尺寸与视频不符时才重置（避免每帧清空 context）
  if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
  }

  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0)
  drawBoxes(ctx, currentBoxes, video.videoWidth)
}

function drawBoxes(ctx, boxes, imgW = 640) {
  if (!boxes?.length) return

  const lw = Math.max(1.5, imgW / 320)
  const fontSize = Math.max(12, Math.round(imgW / 55))
  const tagH = fontSize + 6

  ctx.save()
  for (const box of boxes) {
    const x1 = Math.round(box.x1)
    const y1 = Math.round(box.y1)
    const x2 = Math.round(box.x2)
    const y2 = Math.round(box.y2)
    const color = getColor(box.cls)
    ctx.strokeStyle = color
    ctx.lineWidth = lw
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
    const label = `${box.label} ${(box.conf * 100).toFixed(1)}%`
    ctx.font = `bold ${fontSize}px Inter, sans-serif`
    const tw = ctx.measureText(label).width + 8
    const tagY = y1 > tagH ? y1 - tagH : y1
    ctx.fillStyle = color
    ctx.fillRect(x1, tagY, tw, tagH)
    ctx.fillStyle = '#fff'
    ctx.fillText(label, x1 + 4, tagY + fontSize)
  }
  ctx.restore()
}

// 截帧 → base64 → 推理
async function captureAndInfer() {
  const video = videoRef.value
  const canvas = displayCanvasRef.value
  if (!video || !canvas || !video.videoWidth) return
  // 用一个离屏 canvas 截帧
  const offscreen = document.createElement('canvas')
  offscreen.width = video.videoWidth
  offscreen.height = video.videoHeight
  offscreen.getContext('2d').drawImage(video, 0, 0)
  const b64 = offscreen.toDataURL('image/jpeg', 0.8)
  try {
    const result = await inferImage(b64, props.conf, props.iou)
    const filtered = (result.boxes || []).filter(b => b.conf >= props.conf)
    currentBoxes = filtered          // 绘图用（非响应式，避免每帧 GC 压力）
    currentBoxesRef.value = filtered // 响应式，触发 DetectionList 更新
    lastInferMs.value = result.inference_ms ?? null
    detCount.value = filtered.length
  } catch (_) {
    // 推理失败静默（下一帧重试）
  }
}

// ── 录制功能（MediaRecorder 录制 Canvas 流）────────────────
function startRecording() {
  const canvas = displayCanvasRef.value
  if (!canvas) return
  const stream = canvas.captureStream(30)
  recordedChunks = []
  try {
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' })
  } catch {
    mediaRecorder = new MediaRecorder(stream)
  }
  mediaRecorder.ondataavailable = e => {
    if (e.data.size > 0) recordedChunks.push(e.data)
  }
  mediaRecorder.onstop = saveRecording
  mediaRecorder.start(100)
  recording.value = true
}

function stopRecording() {
  mediaRecorder?.stop()
  recording.value = false
}

function saveRecording() {
  const blob = new Blob(recordedChunks, { type: 'video/webm' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${videoName.value.replace(/\.[^.]+$/, '') ?? 'result'}_detected.webm`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

// 格式化时间
function fmtTime(s) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
}

onUnmounted(() => {
  stopLoop()
  if (videoSrc.value) URL.revokeObjectURL(videoSrc.value)
})
</script>

<style scoped>
.tool-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  background: var(--bg-4);
  color: var(--text-2);
  border: 1px solid var(--border-1);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.tool-btn:hover:not(:disabled) { border-color: var(--border-2); color: var(--text-1); }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.tool-btn--record { color: #ef4444; border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.08); }
.tool-btn--stop { color: var(--text-2); }
.fps-badge {
  font-size: 11px;
  font-family: 'Fira Code', monospace;
  padding: 2px 7px;
  border-radius: 99px;
  background: rgba(16,185,129,0.12);
  color: #10b981;
  border: 1px solid rgba(16,185,129,0.25);
}
.stat-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
  background: rgba(99,102,241,0.12);
  color: var(--accent-light);
  border: 1px solid rgba(99,102,241,0.22);
}
.progress-bar {
  width: 200px;
  accent-color: var(--accent);
  cursor: pointer;
}
.ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border-radius: 50%;
  background: rgba(99,102,241,0.2);
  border: 1px solid rgba(99,102,241,0.35);
  color: var(--accent-light);
  cursor: pointer;
  transition: all 0.15s;
}
.ctrl-btn:hover { background: rgba(99,102,241,0.35); }
.drop-zone {
  transition: border-color 0.15s;
}
</style>
