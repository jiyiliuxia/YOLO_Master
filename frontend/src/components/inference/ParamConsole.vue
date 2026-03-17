<template>
  <!-- 参数调节控制台 -->
  <div class="bento-card p-3 flex-shrink-0" :class="{ 'opacity-50 pointer-events-none': disabled }">
    <div class="text-[11px] font-semibold uppercase tracking-widest text-ink-4 mb-3">参数调节控制台</div>

    <!-- Confidence Slider -->
    <div class="param-row">
      <div class="flex justify-between items-center mb-1.5">
        <label class="param-label">
          <Target :size="12" class="text-accent-light" />
          <span>Confidence</span>
        </label>
        <div class="param-value" :style="{ color: confColor }">{{ conf.toFixed(2) }}</div>
      </div>
      <div class="slider-track">
        <div class="slider-fill" :style="{ width: `${conf * 100}%`, background: confGrad }" />
        <input
          type="range"
          class="slider-input"
          min="0.01" max="1.00" step="0.01"
          :value="conf"
          @input="e => emit('update:conf', +e.target.value)"
        />
      </div>
      <div class="flex justify-between text-[10px] text-ink-4 mt-1">
        <span>0.01</span><span>偏宽松</span><span>1.00</span>
      </div>
    </div>

    <div class="my-2.5 border-t border-border-1" />

    <!-- IoU/NMS Slider -->
    <div class="param-row">
      <div class="flex justify-between items-center mb-1.5">
        <label class="param-label">
          <Layers :size="12" class="text-purple" />
          <span>IoU / NMS</span>
        </label>
        <div class="param-value" style="color: var(--purple)">{{ iou.toFixed(2) }}</div>
      </div>
      <div class="slider-track">
        <div class="slider-fill" :style="{ width: `${iou * 100}%`, background: 'linear-gradient(90deg, #8b5cf6, #6366f1)' }" />
        <input
          type="range"
          class="slider-input"
          min="0.01" max="1.00" step="0.01"
          :value="iou"
          @input="e => emit('update:iou', +e.target.value)"
        />
      </div>
      <div class="flex justify-between text-[10px] text-ink-4 mt-1">
        <span>0.01</span><span>↑重叠去框</span><span>1.00</span>
      </div>
      <div class="mt-1.5 text-[10px] text-ink-4 bg-bg-5 rounded px-2 py-1 leading-relaxed">
        ⚡ 调整 IoU 将触发重新推理（后端 NMS）
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Target, Layers } from 'lucide-vue-next'

const props = defineProps({
  disabled: Boolean,
  conf: { type: Number, default: 0.25 },
  iou: { type: Number, default: 0.45 },
})
const emit = defineEmits(['update:conf', 'update:iou'])

// 置信度颜色：绿→橙→红（随阈值升高变严格，颜色从绿变橙）
const confColor = computed(() => {
  const v = props.conf
  if (v < 0.3) return '#10b981'
  if (v < 0.6) return '#fbbf24'
  return '#f97316'
})

const confGrad = computed(() => {
  const v = props.conf
  if (v < 0.3) return 'linear-gradient(90deg, #10b981, #14b8a6)'
  if (v < 0.6) return 'linear-gradient(90deg, #fbbf24, #f59e0b)'
  return 'linear-gradient(90deg, #f97316, #ef4444)'
})
</script>

<style scoped>
.param-row { user-select: none; }
.param-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-2);
}
.param-value {
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  font-weight: 700;
  min-width: 36px;
  text-align: right;
}
.slider-track {
  position: relative;
  height: 6px;
  background: var(--bg-5);
  border-radius: 99px;
  overflow: visible;
}
.slider-fill {
  position: absolute;
  top: 0; left: 0;
  height: 100%;
  border-radius: 99px;
  pointer-events: none;
  transition: width 0.05s, background 0.3s;
}
.slider-input {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 100%;
  transform: translateY(-50%);
  opacity: 0;
  cursor: pointer;
  margin: 0;
  padding: 0;
  /* 扩大可点击区域 */
  height: 22px;
  top: 50%;
  transform: translateY(-50%);
}
/* thumb 通过外部覆盖 via JS 计算 left 做定制，简单方案用原生 */
</style>
