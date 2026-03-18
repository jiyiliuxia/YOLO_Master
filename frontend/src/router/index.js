import { createRouter, createWebHashHistory } from 'vue-router'
import DataPrepView from '../views/DataPrepView.vue'
import DatasetView from '../views/DatasetView.vue'
import InferenceView from '../views/InferenceView.vue'
import ExportView from '../views/ExportView.vue'

const routes = [
    { path: '/', redirect: '/data-prep' },
    { path: '/data-prep', component: DataPrepView, meta: { title: '数据准备' } },
    { path: '/dataset', component: DatasetView, meta: { title: '数据集管理' } },
    // 后续模块占位
    { path: '/train', component: { template: '<div class="placeholder">🚀 模型训练 — 开发中</div>' } },
    { path: '/export', component: ExportView, meta: { title: '模型导出' } },
    { path: '/inference', component: InferenceView, meta: { title: '推理测试' } },
]

export default createRouter({
    history: createWebHashHistory(),
    routes,
})

