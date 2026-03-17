<template>
  <div class="flex flex-col h-screen bg-bg-0 overflow-hidden">

    <!-- ── Custom Title Bar ─────────────────────────────── -->
    <header
      class="title-bar flex items-center h-10 flex-shrink-0 border-b border-border-1 z-50 select-none px-3 gap-3"
      :class="isTauri ? 'glass' : 'bg-bg-2'"
      data-tauri-drag-region
    >
      <!-- Logo (non-draggable) -->
      <div class="flex items-center gap-2 flex-shrink-0" data-tauri-drag-region="false">
        <div class="w-6 h-6 rounded-md flex items-center justify-center" style="background:linear-gradient(135deg,rgba(99,102,241,.25),rgba(139,92,246,.2));border:1px solid rgba(99,102,241,.35)">
          <svg viewBox="0 0 24 24" fill="none" width="13" height="13">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="url(#tlg)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="tlg" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                <stop stop-color="#6366f1"/><stop offset="1" stop-color="#10b981"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="text-sm font-bold tracking-tight text-ink-1">YOLO<span class="text-accent">Studio</span></span>
      </div>

      <!-- Breadcrumb (draggable region) -->
      <div class="flex items-center gap-1.5 text-xs text-ink-3 font-medium ml-1" data-tauri-drag-region>
        <span class="text-ink-4" data-tauri-drag-region>/</span>
        <span class="text-ink-2" data-tauri-drag-region>{{ currentTitle }}</span>
      </div>

      <!-- Spacer (draggable) -->
      <div class="flex-1" data-tauri-drag-region></div>

      <!-- API Status -->
      <div class="flex items-center gap-1.5 text-xs px-3 py-1 rounded-full mr-2"
        :class="serverOk ? 'bg-em-green/10 text-em-green' : 'bg-em-red/10 text-em-red'">
        <span class="w-1.5 h-1.5 rounded-full flex-shrink-0"
          :class="serverOk ? 'bg-em-green animate-pulse-glow' : 'bg-em-red'"></span>
        {{ serverOk ? 'API Online' : 'API Offline' }}
      </div>

      <!-- Window Controls (Tauri native or visual-only) -->
      <div class="flex items-center gap-1.5">
        <button
          class="w-3 h-3 rounded-full transition-all group relative"
          style="background:#fbbf24"
          @click="minimizeWindow"
          title="最小化"
        >
          <span class="absolute inset-0 rounded-full bg-yellow-600/40 opacity-0 group-hover:opacity-100 flex items-center justify-center">
            <span class="w-1.5 h-px bg-yellow-900 rounded"></span>
          </span>
        </button>
        <button
          class="w-3 h-3 rounded-full transition-all group relative"
          style="background:#10b981"
          @click="maximizeWindow"
          title="最大化 / 还原"
        >
          <span class="absolute inset-0 rounded-full bg-green-700/40 opacity-0 group-hover:opacity-100 flex items-center justify-center">
            <MaximizeIcon :size="6" class="text-green-900"/>
          </span>
        </button>
        <button
          class="w-3 h-3 rounded-full transition-all group relative"
          style="background:#ef4444"
          @click="closeWindow"
          title="关闭"
        >
          <span class="absolute inset-0 rounded-full bg-red-700/40 opacity-0 group-hover:opacity-100 flex items-center justify-center">
            <X :size="6" class="text-red-900"/>
          </span>
        </button>
      </div>
    </header>

    <!-- ── Body ─────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Sidebar ────────────────────────────────────── -->
      <aside
        class="sidebar flex flex-col flex-shrink-0 bg-bg-2 border-r border-border-1 transition-all duration-300 ease-smooth overflow-hidden relative"
        :class="sidebarExpanded ? 'w-56' : 'w-16'"
      >
        <!-- Subtle gradient overlay -->
        <div class="absolute inset-0 pointer-events-none" style="background:linear-gradient(180deg,rgba(99,102,241,.05) 0%,transparent 35%)"></div>

        <!-- Toggle button -->
        <button
          @click="sidebarExpanded = !sidebarExpanded"
          class="absolute -right-3 top-5 w-6 h-6 rounded-full bg-bg-4 border border-border-2 flex items-center justify-center text-ink-3 hover:text-ink-1 hover:border-accent-border transition-all z-10 shadow-card"
        >
          <ChevronLeft v-if="sidebarExpanded" :size="12"/>
          <ChevronRight v-else :size="12"/>
        </button>

        <!-- Nav -->
        <nav class="flex flex-col gap-1 p-2 flex-1 pt-3 relative">
          <router-link
            v-for="item in navItems" :key="item.path"
            :to="item.path"
            class="nav-link group flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all duration-150 relative overflow-visible"
            :class="[$route.path.startsWith(item.path) ? 'nav-active' : 'nav-idle']"
            :title="item.label"
          >
            <component :is="item.icon" :size="17" class="flex-shrink-0 transition-colors" />
            <span
              class="text-xs font-semibold whitespace-nowrap transition-all duration-300 overflow-hidden"
              :class="sidebarExpanded ? 'opacity-100 max-w-full' : 'opacity-0 max-w-0'"
            >{{ item.label }}</span>
            <span v-if="item.soon && sidebarExpanded"
              class="ml-auto text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-accent/10 text-accent-light border border-accent/20"
            >Soon</span>
            <!-- Tooltip for collapsed -->
            <div v-if="!sidebarExpanded"
              class="absolute left-full ml-3 bg-bg-4 border border-border-2 text-ink-2 text-xs font-medium px-2.5 py-1.5 rounded-md shadow-card whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50"
            >{{ item.label }}</div>
          </router-link>
        </nav>

        <!-- Version footer -->
        <div class="px-3 pb-3 relative">
          <div v-if="sidebarExpanded" class="text-[10px] text-ink-4 font-medium border-t border-border-1 pt-2.5">
            v0.2.0 · {{ isTauri ? '🖥 桌面端' : '🌐 浏览器' }}
          </div>
        </div>
      </aside>

      <!-- ── Main Content ───────────────────────────────── -->
      <main class="flex-1 overflow-hidden bg-bg-1">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import {
  Database, Cpu, Download, Layers, FlaskConical,
  ChevronLeft, ChevronRight, X, Maximize2 as MaximizeIcon
} from 'lucide-vue-next'

const route = useRoute()
const serverOk = ref(false)
const sidebarExpanded = ref(window.innerWidth >= 1440)
const isTauri = ref(!!window.__TAURI__)

// ── Window Controls via Tauri API ────────────────────────
let appWindow = null

async function initTauri() {
  if (window.__TAURI__) {
    try {
      const { appWindow: aw } = await import('@tauri-apps/api/window')
      appWindow = aw
    } catch (e) {
      console.warn('[Tauri] Failed to import window API:', e)
    }
  }
}

async function minimizeWindow() {
  if (appWindow) await appWindow.minimize()
}

async function maximizeWindow() {
  if (appWindow) {
    const isMax = await appWindow.isMaximized()
    if (isMax) await appWindow.unmaximize()
    else await appWindow.maximize()
  }
}

async function closeWindow() {
  if (appWindow) await appWindow.close()
}

// ── Responsive sidebar ───────────────────────────────────
const onResize = () => { sidebarExpanded.value = window.innerWidth >= 1440 }

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await initTauri()
  ping()
  setInterval(ping, 5000)
})

onUnmounted(() => { window.removeEventListener('resize', onResize) })

const navItems = [
  { path: '/data-prep',  label: '数据准备',   icon: Layers },
  { path: '/dataset',    label: '数据集管理', icon: Database },
  { path: '/train',      label: '模型训练',   icon: Cpu,          soon: true },
  { path: '/export',     label: '模型导出',   icon: Download,     soon: true },
  { path: '/inference',  label: '推理测试',   icon: FlaskConical },
]

const currentTitle = computed(() => {
  const found = navItems.find(i => route.path.startsWith(i.path))
  return found?.label ?? 'YOLOStudio'
})

async function ping() {
  try {
    await axios.get('http://127.0.0.1:8765/health', { timeout: 2500 })
    serverOk.value = true
  } catch { serverOk.value = false }
}
</script>

<style scoped>
/* tauri drag region is set via data attribute in template */

.nav-idle { color: var(--text-3); }
.nav-idle:hover { color: var(--text-2); background: var(--bg-3); }

.nav-active {
  color: var(--accent-light);
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.2);
}
.nav-active:hover { color: var(--accent-light); }
</style>
