<template>
  <!-- 检测结果列表面板：始终常驻，高度固定，防止有无结果时布局抖动 -->
  <div class="det-list-wrap">

    <!-- 标题栏 -->
    <div class="det-list-header">
      <span class="det-list-title">
        <Target :size="12" />
        检测结果
      </span>
      <!-- 有结果：显示数量和耗时 -->
      <template v-if="boxes && boxes.length > 0">
        <span class="det-count-badge">{{ boxes.length }} 个目标</span>
        <span v-if="inferMs != null" class="det-ms-badge">{{ inferMs }} ms</span>
      </template>
      <!-- 无结果：显示"未检测到" -->
      <span v-else class="det-none-badge">未检测到目标</span>
    </div>

    <!-- 有结果：横向滚动卡片列表 -->
    <div v-if="boxes && boxes.length > 0" class="det-list-body">
      <div
        v-for="(box, i) in boxes"
        :key="i"
        class="det-item"
        :style="{ '--item-color': getColor(box.cls) }"
      >
        <!-- 颜色标识条 -->
        <div class="det-color-bar" />

        <!-- 序号 + 类别 -->
        <div class="det-main">
          <span class="det-idx">#{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="det-label" :title="box.label">{{ box.label }}</span>
        </div>

        <!-- 置信度进度条 -->
        <div class="det-conf-wrap">
          <div class="det-conf-bar">
            <div
              class="det-conf-fill"
              :style="{ width: `${(box.conf * 100).toFixed(0)}%` }"
            />
          </div>
          <span class="det-conf-val">{{ (box.conf * 100).toFixed(1) }}%</span>
        </div>

        <!-- 坐标 -->
        <div class="det-coords">
          <span class="coord-item">x₁<b>{{ box.x1 }}</b></span>
          <span class="coord-item">y₁<b>{{ box.y1 }}</b></span>
          <span class="coord-item">x₂<b>{{ box.x2 }}</b></span>
          <span class="coord-item">y₂<b>{{ box.y2 }}</b></span>
          <span class="coord-item">w<b>{{ box.x2 - box.x1 }}</b></span>
          <span class="coord-item">h<b>{{ box.y2 - box.y1 }}</b></span>
        </div>
      </div>
    </div>

    <!-- 无结果：占位区域（高度与有结果时一致，防止抖动）-->
    <div v-else class="det-empty-body">
      <Target :size="20" class="opacity-15" />
      <span>当前置信度阈值下无检测目标</span>
    </div>

  </div>
</template>

<script setup>
import { Target } from 'lucide-vue-next'

defineProps({
  boxes:   { type: Array,  default: () => [] },
  inferMs: { type: Number, default: null },
})

const PALETTE = [
  '#6366f1','#10b981','#f97316','#3b82f6','#8b5cf6',
  '#ec4899','#14b8a6','#fbbf24','#ef4444','#06b6d4',
]
function getColor(cls) { return PALETTE[(cls ?? 0) % PALETTE.length] }
</script>

<style scoped>
/* 整体容器：固定高度，不随内容变化，避免布局抖动 */
.det-list-wrap {
  flex-shrink: 0;
  height: 140px;          /* 固定高度 — 关键！防止空结果时坍缩 */
  border-top: 1px solid var(--border-1);
  background: var(--bg-2);
  display: flex;
  flex-direction: column;
}

/* 标题栏 */
.det-list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-bottom: 1px solid var(--border-1);
  flex-shrink: 0;
}
.det-list-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-3);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.det-count-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 99px;
  background: rgba(99,102,241,0.15);
  color: var(--accent-light);
  border: 1px solid rgba(99,102,241,0.25);
}
.det-none-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 99px;
  background: rgba(100,100,100,0.12);
  color: var(--text-4);
  border: 1px solid var(--border-1);
}
.det-ms-badge {
  font-size: 10px;
  font-family: 'Fira Code', monospace;
  color: var(--text-4);
  margin-left: auto;
}

/* 有结果：横向滚动列表 */
.det-list-body {
  display: flex;
  flex-direction: row;
  gap: 6px;
  padding: 6px 10px;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  align-items: stretch;
  scrollbar-width: thin;
  scrollbar-color: var(--border-2) transparent;
}
.det-list-body::-webkit-scrollbar { height: 4px; }
.det-list-body::-webkit-scrollbar-track { background: transparent; }
.det-list-body::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 99px; }

/* 无结果占位（高度撑满剩余空间，与有结果时布局等高） */
.det-empty-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-4);
}

/* 每个检测框卡片 */
.det-item {
  flex-shrink: 0;
  width: 185px;
  background: var(--bg-4);
  border: 1px solid var(--border-1);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 5px 8px 5px 10px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.15s;
}
.det-item:hover { border-color: var(--item-color); }

/* 左侧彩色标识条 */
.det-color-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--item-color);
  border-radius: 8px 0 0 8px;
}

/* 序号 + 类别行 */
.det-main {
  display: flex;
  align-items: baseline;
  gap: 5px;
}
.det-idx {
  font-size: 10px;
  font-family: 'Fira Code', monospace;
  color: var(--text-4);
}
.det-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--item-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

/* 置信度进度条 */
.det-conf-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}
.det-conf-bar {
  flex: 1;
  height: 4px;
  background: var(--bg-5);
  border-radius: 99px;
  overflow: hidden;
}
.det-conf-fill {
  height: 100%;
  background: var(--item-color);
  border-radius: 99px;
  transition: width 0.2s ease;
}
.det-conf-val {
  font-size: 11px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: var(--text-2);
  min-width: 38px;
  text-align: right;
}

/* 坐标网格 */
.det-coords {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px 6px;
}
.coord-item {
  font-size: 9.5px;
  color: var(--text-4);
  display: flex;
  gap: 2px;
  align-items: baseline;
}
.coord-item b {
  font-weight: 600;
  font-family: 'Fira Code', monospace;
  color: var(--text-3);
}
</style>
