<template>
  <!-- 模型加载器 -->
  <div class="bento-card p-3 flex-shrink-0">
    <div class="text-[11px] font-semibold uppercase tracking-widest text-ink-4 mb-3">模型引擎</div>

    <!-- 拖拽/点击区域 -->
    <div
      class="drop-zone"
      :class="{ 'drop-zone--dragover': isDragOver, 'drop-zone--loaded': modelLoaded, 'drop-zone--loading': loading }"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
      @click="triggerPicker"
    >
      <input ref="pickerRef" type="file" accept=".pt,.onnx" class="hidden" @change="onFileChange" />

      <!-- 加载中 -->
      <div v-if="loading" class="flex flex-col items-center gap-2">
        <div class="spinner" />
        <span class="text-xs text-ink-3">加载中…</span>
      </div>

      <!-- 已加载 -->
      <div v-else-if="modelLoaded" class="flex flex-col items-center gap-1.5">
        <div class="w-8 h-8 rounded-full bg-em-green/15 flex items-center justify-center">
          <CheckCircle2 :size="18" class="text-em-green" />
        </div>
        <span class="text-xs font-semibold text-em-green">模型已就绪</span>
        <span class="text-[10px] text-ink-4 font-mono truncate max-w-full px-1">{{ shortName }}</span>
        <button class="reopen-btn" @click.stop="triggerPicker">更换模型</button>
      </div>

      <!-- 未加载 -->
      <div v-else class="flex flex-col items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
          <Upload :size="16" class="text-accent-light" />
        </div>
        <span class="text-xs text-ink-3 text-center leading-relaxed">
          拖入或点击选择<br />
          <span class="text-ink-4">.pt / .onnx 模型文件</span>
        </span>
      </div>
    </div>

    <!-- 输入模型路径（手动输入） -->
    <div class="mt-2 relative">
      <input
        v-model="manualPath"
        class="path-input"
        placeholder="或粘贴服务器模型绝对路径…"
        @keydown.enter="loadByPath(manualPath)"
      />
      <button
        v-if="manualPath"
        class="absolute right-2 top-1/2 -translate-y-1/2 text-accent-light hover:text-white text-[11px] font-semibold"
        @click="loadByPath(manualPath)"
      >加载</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CheckCircle2, Upload } from 'lucide-vue-next'
import { loadModel } from '../../api/inference'
import axios from 'axios'

const BASE = 'http://127.0.0.1:8765/inference'

const emit = defineEmits(['loaded', 'error'])

const isDragOver = ref(false)
const loading = ref(false)
const modelLoaded = ref(false)
const loadedPath = ref('')
const manualPath = ref('')
const pickerRef = ref(null)

const shortName = computed(() => {
  if (!loadedPath.value) return ''
  return loadedPath.value.replace(/\\/g, '/').split('/').pop()
})

function triggerPicker() {
  pickerRef.value?.click()
}

async function onDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) await loadByFile(file)
}

async function onFileChange(e) {
  const file = e.target.files[0]
  if (file) await loadByFile(file)
}

// 通过文件对象加载
// Tauri 桌面端：file.path 是本地绝对路径 → 走路径接口
// 浏览器 Web 端：file.path 为 undefined → 走文件上传接口
async function loadByFile(file) {
  if (file.path) {
    // Tauri 环境：直接传路径
    await loadByPath(file.path)
  } else {
    // 浏览器环境：上传文件内容
    await uploadFile(file)
  }
}

// 浏览器端：multipart 文件上传
async function uploadFile(file) {
  const ext = file.name.toLowerCase().split('.').pop()
  if (ext !== 'pt' && ext !== 'onnx') {
    emit('error', '仅支持 .pt 或 .onnx 格式')
    return
  }
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await axios.post(`${BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      // 大模型文件可能需要较长超时
      timeout: 300_000,
    })
    loadedPath.value = file.name
    modelLoaded.value = true
    emit('loaded', data)
  } catch (e) {
    emit('error', `加载失败：${e.response?.data?.detail ?? e.message}`)
  } finally {
    loading.value = false
  }
}

// 通过路径加载
async function loadByPath(path) {
  if (!path) return
  const ext = path.toLowerCase().split('.').pop()
  if (ext !== 'pt' && ext !== 'onnx') {
    emit('error', '仅支持 .pt 或 .onnx 格式')
    return
  }
  loading.value = true
  try {
    const info = await loadModel(path)
    loadedPath.value = path
    modelLoaded.value = true
    manualPath.value = ''
    emit('loaded', info)
  } catch (e) {
    emit('error', `加载失败：${e.response?.data?.detail ?? e.message}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.drop-zone {
  border: 1.5px dashed var(--border-2);
  border-radius: 10px;
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 110px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: var(--bg-4);
}
.drop-zone:hover {
  border-color: var(--accent-border);
  background: var(--bg-5);
}
.drop-zone--dragover {
  border-color: var(--accent);
  background: rgba(99,102,241,0.06);
}
.drop-zone--loaded {
  border-color: rgba(16,185,129,0.35);
  background: rgba(16,185,129,0.04);
}
.drop-zone--loading {
  cursor: wait;
}
.reopen-btn {
  margin-top: 2px;
  font-size: 10px;
  color: var(--text-4);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}
.reopen-btn:hover { color: var(--text-3); }
.path-input {
  width: 100%;
  background: var(--bg-5);
  border: 1px solid var(--border-1);
  border-radius: 7px;
  padding: 6px 48px 6px 10px;
  font-size: 11px;
  color: var(--text-2);
  font-family: 'Fira Code', monospace;
  outline: none;
  transition: border-color 0.15s;
}
.path-input:focus { border-color: var(--accent-border); }
.path-input::placeholder { color: var(--text-4); }
.spinner {
  width: 22px;
  height: 22px;
  border: 2.5px solid var(--border-2);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
