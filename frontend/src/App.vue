<template>
  <div class="app-root">

    <!-- ══ 顶部标题栏 ══════════════════════════════════════ -->
    <header
      class="topbar"
      :class="isTauri ? 'glass' : ''"
      data-tauri-drag-region
    >
      <!-- Logo -->
      <div class="topbar-logo" data-tauri-drag-region="false">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="url(#tlg)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="tlg" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                <stop stop-color="#6366f1"/><stop offset="1" stop-color="#10b981"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="logo-text">YOLO<span>Studio</span></span>
      </div>

      <!-- 左弹性空白 -->
      <div class="flex-1" data-tauri-drag-region></div>

      <!-- ── 中央药丸导航 ── -->
      <nav class="pill-nav" data-tauri-drag-region="false">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.soon ? $route.path : item.path"
          class="pill-item"
          :class="[$route.path.startsWith(item.path) ? 'pill-active' : 'pill-idle', item.soon && 'pill-soon']"
        >
          <component :is="item.icon" :size="13" />
          <span>{{ item.label }}</span>
          <span v-if="item.soon" class="pill-badge">Soon</span>
        </router-link>
      </nav>

      <!-- 右弹性空白 -->
      <div class="flex-1" data-tauri-drag-region></div>

      <!-- 右侧控件 -->
      <div class="topbar-right" data-tauri-drag-region="false">
        <!-- Theme Toggle -->
        <button class="tbar-btn" @click="toggleTheme" :title="isDark ? '切换日间模式' : '切换暗色模式'">
          <Sun v-if="isDark" :size="14" />
          <Moon v-else :size="14" />
        </button>

        <!-- API Status -->
        <div class="api-badge" :class="serverOk ? 'api-ok' : 'api-err'">
          <span class="api-dot" :class="serverOk ? 'dot-ok' : 'dot-err'"></span>
          {{ serverOk ? 'Online' : 'Offline' }}
        </div>

        <!-- Window Controls -->
        <div class="win-controls">
          <button class="wc wc-min" @click="minimizeWindow" title="最小化"></button>
          <button class="wc wc-max" @click="maximizeWindow" title="最大化"></button>
          <button class="wc wc-cls" @click="closeWindow"   title="关闭"></button>
        </div>
      </div>
    </header>

    <!-- ══ 全宽主内容区 ══════════════════════════════════ -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import {
  Database, Cpu, Download, Layers, FlaskConical,
  Sun, Moon
} from 'lucide-vue-next'

const route    = useRoute()
const serverOk = ref(false)
const isTauri  = ref(!!window.__TAURI__)
const isDark   = ref(true)

// ── 主题 ──────────────────────────────────────────────────
function applyTheme(dark) {
  document.documentElement.classList.toggle('light', !dark)
  isDark.value = dark
}
function toggleTheme() {
  const next = !isDark.value
  applyTheme(next)
  try { localStorage.setItem('yolostudio-theme', next ? 'dark' : 'light') } catch {}
}

// ── Tauri 窗口控件 ─────────────────────────────────────────
let appWindow = null
async function initTauri() {
  if (!window.__TAURI__) return
  try {
    const { appWindow: aw } = await import('@tauri-apps/api/window')
    appWindow = aw
  } catch {}
}
async function minimizeWindow() { appWindow?.minimize() }
async function maximizeWindow() {
  if (!appWindow) return
  ;(await appWindow.isMaximized()) ? appWindow.unmaximize() : appWindow.maximize()
}
async function closeWindow() { appWindow?.close() }

// ── 心跳 ──────────────────────────────────────────────────
async function ping() {
  try { await axios.get('http://127.0.0.1:8765/health', { timeout: 2500 }); serverOk.value = true }
  catch { serverOk.value = false }
}

onMounted(async () => {
  await initTauri()
  try { applyTheme(localStorage.getItem('yolostudio-theme') !== 'light') }
  catch { applyTheme(true) }
  ping()
  setInterval(ping, 5000)
})

// ── 导航项 ─────────────────────────────────────────────────
const navItems = [
  { path: '/data-prep',  label: '数据准备',   icon: Layers },
  { path: '/dataset',    label: '数据集管理', icon: Database },
  { path: '/train',      label: '模型训练',   icon: Cpu,          soon: true },
  { path: '/export',     label: '模型导出',   icon: Download },
  { path: '/inference',  label: '推理测试',   icon: FlaskConical },
]
</script>

<style scoped>
/* ── 根容器 ──────────────────────────────────────────────── */
.app-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-0);
}

/* ── 顶部栏 ──────────────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  height: 48px;
  flex-shrink: 0;
  padding: 0 18px;
  gap: 0;
  background: var(--bg-2);
  border-bottom: 1px solid var(--border-1);
  z-index: 50;
  user-select: none;
}

/* Logo */
.topbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.logo-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99,102,241,.22), rgba(139,92,246,.18));
  border: 1px solid rgba(99,102,241,.32);
}
.logo-text {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.4px;
  color: var(--text-1);
}
.logo-text span { color: var(--accent); }

/* ── 中央药丸导航 ──────────────────────────────────────── */
.pill-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border-radius: 99px;
  background: var(--bg-3);
  border: 1px solid var(--border-1);
}
.pill-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 15px;
  border-radius: 99px;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: background .15s, color .15s, box-shadow .15s;
  white-space: nowrap;
  color: var(--text-3);
}
.pill-idle:hover { color: var(--text-2); background: var(--bg-4); }
.pill-active {
  color: #ffffff;
  background: var(--accent);
  box-shadow: 0 2px 10px rgba(99,102,241,.35);
}
.pill-active:hover { color: #fff; }
.pill-soon {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}
.pill-badge {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .4px;
  padding: 1px 5px;
  border-radius: 99px;
  background: rgba(99,102,241,.15);
  color: var(--accent-light);
  border: 1px solid rgba(99,102,241,.2);
}

/* ── 右侧控件 ────────────────────────────────────────────── */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.tbar-btn {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  border: 1px solid var(--border-2);
  background: var(--bg-3);
  color: var(--text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color .15s, border-color .15s, background .15s;
}
.tbar-btn:hover { color: var(--text-1); border-color: var(--accent-border); background: var(--bg-4); }

/* API badge */
.api-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 99px;
}
.api-ok  { background: rgba(16,185,129,.1); color: #10b981; }
.api-err { background: rgba(239,68,68,.1);  color: #ef4444; }
.api-dot { width: 6px; height: 6px; border-radius: 99px; }
.dot-ok  { background: #10b981; animation: pulse 2s infinite; }
.dot-err { background: #ef4444; }

@keyframes pulse {
  0%,100% { opacity:1; } 50% { opacity:.4; }
}

/* Window controls */
.win-controls { display: flex; align-items: center; gap: 6px; padding-left: 6px; }
.wc {
  width: 12px; height: 12px;
  border-radius: 99px; border: none;
  cursor: pointer; transition: filter .15s;
}
.wc:hover { filter: brightness(.75); }
.wc-min { background: #fbbf24; }
.wc-max { background: #10b981; }
.wc-cls { background: #ef4444; }

/* ── 主内容区（全宽）────────────────────────────────────── */
.main-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-1);
}

/* ── 日间模式微调 ─────────────────────────────────────── */
:global(html.light) .topbar {
  background: #ffffff;
  border-bottom-color: rgba(0,0,0,.08);
  box-shadow: 0 1px 8px rgba(0,0,0,.06);
}
:global(html.light) .pill-nav {
  background: #f0f0fa;
  border-color: rgba(0,0,0,.09);
}
:global(html.light) .pill-idle { color: #6565a0; }
:global(html.light) .pill-idle:hover { background: #e6e6f5; color: #1a1a2e; }
:global(html.light) .tbar-btn {
  background: #f5f5ff;
  border-color: rgba(0,0,0,.1);
  color: #6565a0;
}
:global(html.light) .tbar-btn:hover { background: #eeeeff; color: #1a1a2e; }

/* ── 路由过渡 ─────────────────────────────────────────── */
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
