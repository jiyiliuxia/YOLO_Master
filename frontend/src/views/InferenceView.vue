<template>
  <div class="page-root">
    <!-- ── 页头 ─────────────────────────────────────────── -->
    <div class="page-header">
      <h1 class="page-title flex items-center gap-2">
        <FlaskConical :size="20" class="text-accent" />
        推理测试台
        <span class="text-xs font-normal text-ink-3 ml-1">Inference &amp; Validation</span>
      </h1>
      <p class="page-sub">加载 .pt / .onnx 模型，拖入图片或视频，实时查看检测结果</p>
    </div>

    <!-- ── 主体三栏 ────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden gap-0 mt-4">

      <!-- ① 左侧控制面板 280px -->
      <aside class="w-[280px] flex-shrink-0 flex flex-col gap-3 px-4 pb-4 overflow-y-auto scroll-y border-r border-border-1">

        <!-- 模型加载 -->
        <ModelLoader @loaded="onModelLoaded" @error="onModelError" />

        <!-- 参数控制台（仅模型加载后激活） -->
        <ParamConsole
          :disabled="!modelInfo.loaded"
          :conf="conf"
          :iou="iou"
          @update:conf="onConfChange"
          @update:iou="onIouChange"
        />

        <!-- 模式切换 -->
        <div class="bento-card p-3 flex-shrink-0">
          <div class="text-[11px] font-semibold uppercase tracking-widest text-ink-4 mb-2">测试模式</div>
          <div class="flex gap-2">
            <button
              class="mode-btn flex-1"
              :class="mode === 'image' ? 'mode-active' : 'mode-idle'"
              @click="mode = 'image'"
            >
              <ImageIcon :size="14" /><span>图像</span>
            </button>
            <button
              class="mode-btn flex-1"
              :class="mode === 'video' ? 'mode-active' : 'mode-idle'"
              @click="mode = 'video'"
            >
              <Video :size="14" /><span>视频</span>
            </button>
            <button
              class="mode-btn flex-1"
              :class="mode === 'camera' ? 'mode-active' : 'mode-idle'"
              @click="mode = 'camera'"
            >
              <Camera :size="14" /><span>摄像头</span>
            </button>
          </div>
        </div>

        <!-- 图像模式：文件列表 -->
        <ImageFileList
          v-if="mode === 'image'"
          :files="imageFiles"
          :selected-index="selectedIdx"
          :model-loaded="modelInfo.loaded"
          @select="selectImage"
          @add="handleImageAdd"
          @remove="removeImage"
          @clear="clearImages"
        />

        <!-- 模型信息小卡片 -->
        <div v-if="modelInfo.loaded" class="bento-card p-3 flex-shrink-0">
          <div class="text-[11px] font-semibold uppercase tracking-widest text-ink-4 mb-2">模型信息</div>
          <div class="space-y-1.5">
            <div class="flex justify-between text-xs">
              <span class="text-ink-3">后端</span>
              <span class="font-mono text-accent-light text-[11px]">{{ modelInfo.backend }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-ink-3">类别数</span>
              <span class="font-mono text-ink-2">{{ modelInfo.num_classes }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-ink-3">输入尺寸</span>
              <span class="font-mono text-ink-2">{{ modelInfo.input_size?.join('×') ?? '-' }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ② 右侧预览区 flex-1 -->
      <main class="flex-1 flex flex-col overflow-hidden bg-bg-1">

        <!-- 图像模式预览 -->
        <ImagePreviewPanel
          v-if="mode === 'image'"
          :file-item="imageFiles[selectedIdx]"
          :boxes="filteredBoxes"
          :conf="conf"
          :inferring="inferring"
          @export="exportCurrentImage"
        />

        <!-- 视频模式预览 -->
        <VideoTestPanel
          v-else-if="mode === 'video'"
          :model-loaded="modelInfo.loaded"
          :conf="conf"
          :iou="iou"
        />

        <!-- 摄像头实时流模式 -->
        <CameraPanel
          v-else-if="mode === 'camera'"
          :model-loaded="modelInfo.loaded"
          :conf="conf"
          :iou="iou"
        />

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { FlaskConical, ImageIcon, Video, Camera } from 'lucide-vue-next'
import { debounce } from '../utils/debounce'

import ModelLoader from '../components/inference/ModelLoader.vue'
import ParamConsole from '../components/inference/ParamConsole.vue'
import ImageFileList from '../components/inference/ImageFileList.vue'
import ImagePreviewPanel from '../components/inference/ImagePreviewPanel.vue'
import VideoTestPanel from '../components/inference/VideoTestPanel.vue'
import CameraPanel from '../components/inference/CameraPanel.vue'

import { inferImage } from '../api/inference'

// ── 状态 ─────────────────────────────────────────────────
const mode = ref('image')
const modelInfo = ref({ loaded: false })

// 参数
const conf = ref(0.25)
const iou = ref(0.45)

// 图像列表
// fileItem: { name, file, objectUrl, b64, rawBoxes, status, inferMs }
const imageFiles = ref([])
const selectedIdx = ref(0)
const inferring = ref(false)

// ── 当前选中图像的过滤后 boxes ────────────────────────────
const filteredBoxes = computed(() => {
  const item = imageFiles.value[selectedIdx.value]
  if (!item || !item.rawBoxes) return []
  return item.rawBoxes.filter(b => b.conf >= conf.value)
})

// ── 事件处理 ─────────────────────────────────────────────

function onModelLoaded(info) {
  modelInfo.value = { loaded: true, ...info }
  ElMessage.success(`模型加载成功：${info.backend} · ${info.num_classes} 类`)
}

function onModelError(msg) {
  ElMessage.error(msg)
}

// Confidence 变更 → 仅前端过滤（filteredBoxes computed 自动更新 → canvas 重绘）
function onConfChange(val) {
  conf.value = val
}

// IoU 变更 → debounce 300ms 后触发重推理
const _debouncedIouInfer = debounce(() => {
  const idx = selectedIdx.value
  const item = imageFiles.value[idx]
  if (item && item.b64 && modelInfo.value.loaded) {
    runInfer(idx, iou.value)
  }
}, 300)

function onIouChange(val) {
  iou.value = val
  _debouncedIouInfer()
}

// 添加图像文件
async function handleImageAdd(files) {
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue

    // push 进响应式数组，之后通过索引操作确保 Vue 追踪
    imageFiles.value.push({
      name: file.name,
      file,
      objectUrl: URL.createObjectURL(file),
      b64: null,
      rawBoxes: [],
      status: 'idle',
      inferMs: null,
    })

    const idx = imageFiles.value.length - 1
    // 先选中让预览区切到该图
    selectedIdx.value = idx

    if (modelInfo.value.loaded) {
      await runInfer(idx, iou.value)
    }
  }
}

function selectImage(idx) {
  selectedIdx.value = idx
}

function removeImage(idx) {
  URL.revokeObjectURL(imageFiles.value[idx].objectUrl)
  imageFiles.value.splice(idx, 1)
  if (selectedIdx.value >= imageFiles.value.length) {
    selectedIdx.value = Math.max(0, imageFiles.value.length - 1)
  }
}

function clearImages() {
  imageFiles.value.forEach(f => URL.revokeObjectURL(f.objectUrl))
  imageFiles.value = []
  selectedIdx.value = 0
}

// ── 推理核心 ─────────────────────────────────────────────
/**
 * 接受索引（而非 item 对象），通过 imageFiles.value[idx] 即 Vue 3 响应式 Proxy 修改属性，
 * 确保 status / rawBoxes / inferMs 的变更触发 computed filteredBoxes 重算 → canvas 重绘。
 *
 * ❌ 错误写法：runInfer(item, ...) 然后 item.status = 'done'
 *    → item 是 Plain Object，绕过 Proxy，Vue 不感知变化
 * ✅ 正确写法：runInfer(idx, ...) 然后 imageFiles.value[idx].status = 'done'
 *    → 通过 Proxy 写入，Vue 检测到变化并触发更新
 */
async function runInfer(idx, iouVal) {
  const item = imageFiles.value[idx]   // 响应式 Proxy
  if (!item) return

  item.status = 'inferring'            // Proxy 写入 → Vue 追踪
  inferring.value = true
  try {
    if (!item.b64) {
      item.b64 = await fileToBase64(item.file)
    }
    const result = await inferImage(item.b64, conf.value, iouVal)
    // 确保每次都通过 Proxy 写 rawBoxes，触发 filteredBoxes computed 更新
    imageFiles.value[idx].rawBoxes = result.boxes
    imageFiles.value[idx].inferMs = result.inference_ms
    imageFiles.value[idx].status = 'done'
  } catch (e) {
    imageFiles.value[idx].status = 'error'
    ElMessage.error(`推理失败：${e.response?.data?.detail ?? e.message}`)
  } finally {
    inferring.value = false
  }
}

// 导出当前带框图像（由 ImagePreviewPanel 触发，这里透传）
function exportCurrentImage() {}

// ── 工具函数 ─────────────────────────────────────────────
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
</script>

<style scoped>
.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-idle {
  background: var(--bg-4);
  color: var(--text-3);
  border-color: var(--border-1);
}
.mode-idle:hover {
  color: var(--text-2);
  border-color: var(--border-2);
}
.mode-active {
  background: rgba(99,102,241,0.15);
  color: var(--accent-light);
  border-color: rgba(99,102,241,0.35);
}
</style>
