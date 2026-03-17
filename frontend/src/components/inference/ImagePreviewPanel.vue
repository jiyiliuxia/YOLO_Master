<template>
  <div class="flex flex-col h-full overflow-hidden">

    <!-- 空白提示 -->
    <div v-if="!fileItem" class="flex-1 flex flex-col items-center justify-center text-ink-4 gap-3">
      <ImageIcon :size="48" class="opacity-20" />
      <span class="text-sm">从左侧列表选择图片，或拖入图片开始</span>
    </div>

    <!-- 预览区 -->
    <div v-else class="flex-1 flex flex-col overflow-hidden">

      <!-- 工具栏 -->
      <div class="flex items-center gap-3 px-5 py-2.5 border-b border-border-1 flex-shrink-0">
        <span class="text-sm font-semibold text-ink-2 truncate flex-1">{{ fileItem.name }}</span>

        <!-- 推理耗时 -->
        <span v-if="fileItem.inferMs" class="text-xs font-mono text-ink-3">
          ⚡ {{ fileItem.inferMs }} ms
        </span>

        <!-- 显示框数量 -->
        <span v-if="fileItem.status === 'done'" class="stat-badge">
          {{ boxes.length }} / {{ fileItem.rawBoxes?.length }} 框
        </span>

        <!-- Conf 滑块提示 -->
        <span class="text-xs text-ink-4">阈值 conf ≥ {{ conf.toFixed(2) }}</span>

        <!-- 导出按钮 -->
        <button
          class="export-btn"
          :disabled="fileItem.status !== 'done'"
          @click="exportCanvas"
        >
          <Download :size="13" />
          导出带框图
        </button>
      </div>

      <!-- Canvas 容器 -->
      <div
        ref="containerRef"
        class="flex-1 relative overflow-hidden flex items-center justify-center bg-[#0a0a10]"
      >
        <!-- 推理中遮罩 -->
        <div v-if="inferring" class="absolute inset-0 flex items-center justify-center z-10 bg-bg-0/60 backdrop-blur-sm">
          <div class="flex flex-col items-center gap-3">
            <div class="big-spinner" />
            <span class="text-sm text-ink-2 font-medium">推理中…</span>
          </div>
        </div>

        <canvas
          ref="canvasRef"
          class="max-w-full max-h-full object-contain"
          style="image-rendering: crisp-edges;"
        />
      </div>

      <!-- 检测结果列表（着降于 canvas 下方） -->
      <DetectionList
        :boxes="boxes"
        :infer-ms="fileItem?.inferMs"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ImageIcon, Download } from 'lucide-vue-next'
import DetectionList from './DetectionList.vue'

const props = defineProps({
  fileItem: { type: Object, default: null },
  boxes: { type: Array, default: () => [] },
  conf: { type: Number, default: 0.25 },
  inferring: Boolean,
})

const canvasRef = ref(null)
const containerRef = ref(null)

// 颜色调色板（按 class idx 循环）
const PALETTE = [
  '#6366f1', '#10b981', '#f97316', '#3b82f6', '#8b5cf6',
  '#ec4899', '#14b8a6', '#fbbf24', '#ef4444', '#06b6d4',
]

function getColor(cls) {
  return PALETTE[cls % PALETTE.length]
}

// 渲染逻辑
// 策略：canvas 始终以原图原始分辨率绘制，boxes 直接用原图像素坐标。
// CSS max-w-full/max-h-full 负责视觉缩小，彻底避免两次 scale 叠加导致坐标错位。
async function render() {
  const canvas = canvasRef.value
  if (!canvas || !props.fileItem) return

  const ctx = canvas.getContext('2d')
  const img = new Image()
  img.src = props.fileItem.objectUrl

  // 确保图像元数据已加载（不依赖 img.complete 的 naturalWidth 时机问题）
  await new Promise((resolve, reject) => {
    if (img.complete && img.naturalWidth > 0) return resolve()
    img.onload = resolve
    img.onerror = reject
  })

  if (!img.naturalWidth || !img.naturalHeight) return

  // canvas 固定为原图分辨率
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight

  // 绘制底图（1:1，无缩放）
  ctx.drawImage(img, 0, 0)

  // 绘制检测框（坐标直接用原图像素，scale = 1）
  drawBoxes(ctx, props.boxes, img.naturalWidth)
}

// boxes 坐标已是原图像素坐标，直接绘制
// imgW 用于自适应线宽和字体大小（高分辨率图用更粗的线）
function drawBoxes(ctx, boxes, imgW = 640) {
  if (!boxes || !boxes.length) return

  // 自适应粗细：参考宽度 640px，比例缩放
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

    // 边框
    ctx.strokeStyle = color
    ctx.lineWidth = lw
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

    // 标签
    const label = `${box.label} ${(box.conf * 100).toFixed(1)}%`
    ctx.font = `bold ${fontSize}px Inter, sans-serif`
    const textW = ctx.measureText(label).width + 8
    const tagY = y1 > tagH ? y1 - tagH : y1
    ctx.fillStyle = color
    ctx.fillRect(x1, tagY, textW, tagH)
    ctx.fillStyle = '#fff'
    ctx.fillText(label, x1 + 4, tagY + fontSize)
  }
  ctx.restore()
}

// 导出带框图像
function exportCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.toBlob(blob => {
    if (!blob) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    const name = props.fileItem?.name?.replace(/\.[^.]+$/, '') ?? 'result'
    a.download = `${name}_detected.jpg`
    a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 1000)
  }, 'image/jpeg', 0.95)
}

// 监听触发重渲染
watch(
  () => [props.fileItem?.objectUrl, props.boxes],
  async () => {
    await nextTick()
    render()
  },
  { deep: true }
)

// ResizeObserver 适配窗口大小变化
let ro = null
onMounted(() => {
  ro = new ResizeObserver(() => render())
  if (containerRef.value) ro.observe(containerRef.value)
})
onUnmounted(() => ro?.disconnect())
</script>

<style scoped>
.stat-badge {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
  background: rgba(99,102,241,0.12);
  color: var(--accent-light);
  border: 1px solid rgba(99,102,241,0.22);
}
.export-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(16,185,129,0.12);
  color: #10b981;
  border: 1px solid rgba(16,185,129,0.3);
  cursor: pointer;
  transition: all 0.15s;
}
.export-btn:hover:not(:disabled) {
  background: rgba(16,185,129,0.22);
}
.export-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.big-spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border-2);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
