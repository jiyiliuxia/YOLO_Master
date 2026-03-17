import { createRouter, createWebHashHistory } from 'vue-router'
import DataPrepView from '../views/DataPrepView.vue'
import DatasetView from '../views/DatasetView.vue'

const routes = [
    { path: '/', redirect: '/data-prep' },
    { path: '/data-prep', component: DataPrepView, meta: { title: '数据准备' } },
    { path: '/dataset', component: DatasetView, meta: { title: '数据集管理' } },
    // 后续模块占位
    { path: '/train', component: { template: '<div class="placeholder">🚀 模型训练 — 开发中</div>' } },
    { path: '/export', component: { template: '<div class="placeholder">📦 模型导出 — 开发中</div>' } },
    { path: '/inference', component: { template: '<div class="placeholder">🔬 推理测试 — 开发中</div>' } },
]

export default createRouter({
    history: createWebHashHistory(),
    routes,
})
