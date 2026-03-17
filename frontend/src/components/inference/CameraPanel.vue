<template>
  <div class="flex flex-col h-full overflow-hidden">

    <!-- 未加载模型提示 -->
    <div v-if="!modelLoaded" class="flex-1 flex flex-col items-center justify-center text-ink-4 gap-3">
      <Camera :size="48" class="opacity-20" />
      <span class="text-sm">请先在左侧加载模型</span>
    </div>

    <template v-else>
      <!-- 工具栏 -->
      <div class="flex items-center gap-3 px-5 py-2.5 border-b border-border-1 flex-shrink-0 flex-wrap">

        <!-- 摄像头选择器 -->
        <div class="flex items-center gap-2">
          <Camera :size="13" class="text-ink-3" />
          <select
            v-model="selectedDeviceId"
            class="cam-select"
            @change="switchCamera"
          >
            <option v-if="cameras.length === 0" value="">正在扫描摄像头…</option>
            <option v-for="cam in cameras" :key="cam.deviceId" :value="cam.deviceId">
              {{ cam.label || `摄像头 ${cam.deviceId.slice(0, 8)}` }}
            </option>
          </select>
        </div>

        <!-- 分辨率 -->
        <div class="flex items-center gap-2">
          <select v-model="resolution" class="cam-select" @change="switchCamera">
            <option value="640x480">640 × 480</option>
            <option value="1280x720">1280 × 720</option>
            <option value="1920x1080">1920 × 1080</option>
          </select>
        </div>

        <div class="flex-1" />

        <!-- FPS 指示器 -->
        <span v-if="streaming" class="fps-badge">{{ displayFps }} FPS</span>

        <!-- 检测框数 -->
        <span v-if="detCount > 0" class="stat-badge">{{ detCount }} 框</span>

        <!-- 推理开关 -->
        <label class="flex items-center gap-1.5 text-xs text-ink-3 cursor-pointer select-none">
          <input type="checkbox" v-model="inferEnabled" class="accent-indigo-500" />
          实时推理
        </label>

        <!-- 开启 / 关闭摄像头 -->
        <button
          v-if="!streaming"
          class="tool-btn tool-btn--start"
          :disabled="cameras.length === 0"
          @click="startCamera"
        >
          <Power :size="13" /> 开启摄像头
        </button>
        <button v-else class="tool-btn tool-btn--stop" @click="stopCamera">
          <PowerOff :size="13" /> 关闭摄像头
        </button>
      </div>

      <!-- 视频 + Canvas 叠加区域 -->
      <div class="flex-1 relative overflow-hidden flex items-center justify-center bg-[#0a0a10]">

        <!-- 未开启时的提示 -->
        <div v-if="!streaming" class="flex flex-col items-center gap-4 text-ink-4">
          <div class="cam-idle-icon">
            <Camera :size="40" class="opacity-30" />
          </div>
          <span class="text-sm text-ink-3">点击「开启摄像头」开始实时推理</span>
          <span class="text-xs text-ink-4">需要浏览器摄像头访问权限</span>
        </div>

        <!-- 隐藏 video 元素（仅用于解码摄像头帧） -->
        <video
          ref="videoRef"
          class="hidden"
          autoplay
          playsinline
          muted
        />

        <!-- Canvas 渲染（摄像头帧 + 检测框叠加） -->
        <canvas
          v-show="streaming"
          ref="canvasRef"
          class="max-w-full max-h-full object-contain"
          style="image-rendering: crisp-edges;"
        />

        <!-- 错误提示 -->
        <div v-if="errorMsg" class="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-red-400 bg-bg-3/90 px-3 py-1.5 rounded-lg border border-red-500/20">
          {{ errorMsg }}
        </div>
      </div>

      <!-- 检测结果列表 -->
      <DetectionList :boxes="displayBoxes" :infer-ms="lastInferMs" />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Camera, Power, PowerOff } from 'lucide-vue-next'
import { inferImage } from '../../api/inference'
import DetectionList from './DetectionList.vue'

const props = defineProps({
  modelLoaded: Boolean,
  conf: { type: Number, default: 0.25 },
  iou:  { type: Number, default: 0.45 },
})

// ── 摄像头设备列表 ─────────────────────────────────────────
const cameras = ref([])
const selectedDeviceId = ref('')
const resolution = ref('1280x720')
const streaming = ref(false)
const errorMsg = ref('')

// ── 推理状态 ──────────────────────────────────────────────
const inferEnabled = ref(true)
const detCount = ref(0)
const lastInferMs = ref(null)
const displayFps = ref(0)

const currentBoxesRef = ref([])
let currentBoxes = []

const displayBoxes = computed(() =>
  currentBoxesRef.value.filter(b => b.conf >= props.conf)
)

// ── DOM 引用 ──────────────────────────────────────────────
const videoRef = ref(null)
const canvasRef = ref(null)

// ── 颜色调色板 ────────────────────────────────────────────
const PALETTE = [
  '#6366f1','#10b981','#f97316','#3b82f6','#8b5cf6',
  '#ec4899','#14b8a6','#fbbf24','#ef4444','#06b6d4',
]
function getColor(cls) { return PALETTE[(cls ?? 0) % PALETTE.length] }

// ── 推理循环变量 ──────────────────────────────────────────
let animFrame = null
let lastInferTime = 0
const INFER_INTERVAL_MS = 120    // ~8fps 推理
let fpsCounter = 0
let fpsTimer = 0
let activeStream = null          // 当前 MediaStream 引用

// ── 枚举可用摄像头 ────────────────────────────────────────
async function listCameras() {
  try {
    // 先请求权限，才能拿到完整 label
    await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices.filter(d => d.kind === 'videoinput')
    if (cameras.value.length > 0 && !selectedDeviceId.value) {
      selectedDeviceId.value = cameras.value[0].deviceId
    }
  } catch (e) {
    errorMsg.value = `获取摄像头列表失败：${e.message}`
  }
}

// ── 开启摄像头 ────────────────────────────────────────────
async function startCamera() {
  errorMsg.value = ''
  const [w, h] = resolution.value.split('x').map(Number)
  const constraints = {
    video: {
      deviceId: selectedDeviceId.value ? { exact: selectedDeviceId.value } : undefined,
      width: { ideal: w },
      height: { ideal: h },
    },
    audio: false,
  }
  try {
    activeStream = await navigator.mediaDevices.getUserMedia(constraints)
    const video = videoRef.value
    video.srcObject = activeStream
    await video.play()
    streaming.value = true

    // Canvas 尺寸随视频初始化
    video.onloadedmetadata = () => {
      const canvas = canvasRef.value
      if (canvas) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
      }
    }
    startLoop()
  } catch (e) {
    errorMsg.value = `摄像头开启失败：${e.message}`
  }
}

// ── 关闭摄像头 ────────────────────────────────────────────
function stopCamera() {
  stopLoop()
  if (activeStream) {
    activeStream.getTracks().forEach(t => t.stop())
    activeStream = null
  }
  const video = videoRef.value
  if (video) video.srcObject = null
  streaming.value = false
  currentBoxes = []
  currentBoxesRef.value = []
  detCount.value = 0
}

// ── 切换摄像头 / 分辨率 ───────────────────────────────────
async function switchCamera() {
  if (streaming.value) {
    stopCamera()
    await startCamera()
  }
}

// ── 渲染循环（rAF 驱动）──────────────────────────────────
function startLoop() {
  fpsTimer = Date.now()
  fpsCounter = 0

  function loop() {
    const video = videoRef.value
    const canvas = canvasRef.value
    if (!video || !canvas || !streaming.value) return

    // 同步 canvas 尺寸（分辨率切换后）
    if (canvas.width !== video.videoWidth && video.videoWidth > 0) {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
    }

    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    drawBoxes(ctx, currentBoxes, video.videoWidth)

    // FPS 统计
    fpsCounter++
    const now = Date.now()
    if (now - fpsTimer >= 1000) {
      displayFps.value = fpsCounter
      fpsCounter = 0
      fpsTimer = now
    }

    // 限速推理
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
  displayFps.value = 0
}

// ── 截帧推理 ─────────────────────────────────────────────
async function captureAndInfer() {
  const video = videoRef.value
  if (!video || !video.videoWidth) return

  const offscreen = document.createElement('canvas')
  offscreen.width = video.videoWidth
  offscreen.height = video.videoHeight
  offscreen.getContext('2d').drawImage(video, 0, 0)
  const b64 = offscreen.toDataURL('image/jpeg', 0.75)

  try {
    const result = await inferImage(b64, props.conf, props.iou)
    const filtered = (result.boxes || []).filter(b => b.conf >= props.conf)
    currentBoxes = filtered
    currentBoxesRef.value = filtered
    lastInferMs.value = result.inference_ms ?? null
    detCount.value = filtered.length
  } catch (_) {
    // 静默失败，下一帧重试
  }
}

// ── 绘制检测框（自适应线宽/字体）──────────────────────────
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

// ── 生命周期 ─────────────────────────────────────────────
onMounted(() => {
  listCameras()
  // 监听设备变化（插拔摄像头）
  navigator.mediaDevices?.addEventListener('devicechange', listCameras)
})

onUnmounted(() => {
  stopCamera()
  navigator.mediaDevices?.removeEventListener('devicechange', listCameras)
})
</script>

<style scoped>
.cam-select {
  background: var(--bg-4);
  border: 1px solid var(--border-1);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  color: var(--text-2);
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}
.cam-select:hover, .cam-select:focus { border-color: var(--border-2); }

.tool-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border-1);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.tool-btn--start {
  background: rgba(99,102,241,0.12);
  color: var(--accent-light);
  border-color: rgba(99,102,241,0.3);
}
.tool-btn--start:hover:not(:disabled) {
  background: rgba(99,102,241,0.22);
}
.tool-btn--stop {
  background: rgba(239,68,68,0.1);
  color: #ef4444;
  border-color: rgba(239,68,68,0.3);
}
.tool-btn--stop:hover { background: rgba(239,68,68,0.2); }

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

.cam-idle-icon {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: var(--bg-3);
  border: 1px dashed var(--border-2);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
