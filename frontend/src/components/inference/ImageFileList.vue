<template>
  <div class="bento-card p-3 flex-1 flex flex-col min-h-0">
    <div class="flex items-center justify-between mb-2">
      <div class="text-[11px] font-semibold uppercase tracking-widest text-ink-4">测试图像</div>
      <div class="flex gap-1.5">
        <!-- 添加图片按钮 -->
        <button class="icon-btn" title="添加图片" @click="triggerPicker">
          <Plus :size="13" />
        </button>
        <!-- 清空 -->
        <button class="icon-btn" title="清空列表" :disabled="!files.length" @click="emit('clear')">
          <Trash2 :size="13" />
        </button>
      </div>
    </div>

    <!-- 拖拽提示（列表为空时）-->
    <div
      v-if="!files.length"
      class="drop-zone flex-1"
      :class="{ 'drop-zone--over': isDragOver, 'opacity-50': !modelLoaded }"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
      @click="triggerPicker"
    >
      <ImageIcon :size="24" class="text-ink-4 mb-2" />
      <span class="text-xs text-ink-4 text-center leading-relaxed">
        拖入图片或点击添加<br />.jpg / .png / .bmp / .webp
      </span>
    </div>

    <!-- 文件列表 -->
    <div
      v-else
      class="flex-1 overflow-y-auto scroll-y space-y-1"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @drop.prevent="onDrop"
    >
      <div
        v-for="(item, idx) in files"
        :key="idx"
        class="file-item"
        :class="{ 'file-item--active': selectedIndex === idx }"
        @click="emit('select', idx)"
      >
        <!-- 缩略图 -->
        <img :src="item.objectUrl" class="thumbnail" />

        <!-- 信息 -->
        <div class="flex-1 min-w-0">
          <div class="text-xs font-medium text-ink-2 truncate">{{ item.name }}</div>
          <div class="flex items-center gap-1.5 mt-0.5">
            <!-- 推理状态 badge -->
            <span v-if="item.status === 'inferring'" class="status-badge status-inferring">
              <div class="spinner-tiny" />推理中
            </span>
            <span v-else-if="item.status === 'done'" class="status-badge status-done">
              {{ item.rawBoxes?.length ?? 0 }} det
            </span>
            <span v-else-if="item.status === 'error'" class="status-badge status-error">错误</span>
            <span v-else class="status-badge status-idle">待推理</span>

            <!-- 推理耗时 -->
            <span v-if="item.inferMs" class="text-[10px] text-ink-4 font-mono">{{ item.inferMs }}ms</span>
          </div>
        </div>

        <!-- 删除按钮 -->
        <button class="del-btn" @click.stop="emit('remove', idx)">
          <X :size="11" />
        </button>
      </div>
    </div>

    <!-- 隐藏 file input -->
    <input
      ref="pickerRef"
      type="file"
      class="hidden"
      accept="image/*"
      multiple
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Trash2, ImageIcon, X } from 'lucide-vue-next'

defineProps({
  files: { type: Array, default: () => [] },
  selectedIndex: { type: Number, default: 0 },
  modelLoaded: Boolean,
})
const emit = defineEmits(['select', 'add', 'remove', 'clear'])

const isDragOver = ref(false)
const pickerRef = ref(null)

function triggerPicker() {
  pickerRef.value?.click()
}

function onDrop(e) {
  isDragOver.value = false
  const files = [...e.dataTransfer.files]
  if (files.length) emit('add', files)
}

function onFileChange(e) {
  const files = [...e.target.files]
  if (files.length) emit('add', files)
  e.target.value = ''
}
</script>

<style scoped>
.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1.5px dashed var(--border-2);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  padding: 24px 12px;
  min-height: 100px;
}
.drop-zone:hover, .drop-zone--over {
  border-color: var(--accent-border);
  background: rgba(99,102,241,0.04);
}
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.file-item:hover { background: var(--bg-4); }
.file-item--active {
  background: rgba(99,102,241,0.1);
  border-color: rgba(99,102,241,0.25);
}
.thumbnail {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: var(--bg-5);
}
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px;
  border-radius: 6px;
  border: 1px solid var(--border-1);
  background: var(--bg-4);
  color: var(--text-3);
  cursor: pointer;
  transition: all 0.12s;
}
.icon-btn:hover { color: var(--text-1); border-color: var(--border-2); }
.icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.del-btn {
  display: flex;
  align-items: center;
  color: var(--text-4);
  background: none;
  border: none;
  cursor: pointer;
  padding: 3px;
  border-radius: 4px;
  transition: color 0.12s;
  flex-shrink: 0;
}
.del-btn:hover { color: var(--red); }
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 99px;
}
.status-inferring { background: rgba(99,102,241,0.15); color: var(--accent-light); }
.status-done { background: rgba(16,185,129,0.12); color: #10b981; }
.status-error { background: rgba(239,68,68,0.12); color: #ef4444; }
.status-idle { background: var(--bg-5); color: var(--text-4); }
.spinner-tiny {
  width: 8px; height: 8px;
  border: 1.5px solid var(--accent-border);
  border-top-color: var(--accent-light);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
