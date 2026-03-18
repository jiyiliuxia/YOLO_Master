/**
 * api/index.js — Axios + SSE 封装
 * 所有后端请求从这里发出，方便统一切换端口。
 */
import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8765'

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
})

// 请求拦截（可扩展 Auth）
api.interceptors.response.use(
    res => res.data,
    err => Promise.reject(err?.response?.data || err.message)
)

export default api

// ── SSE 工具方法 ─────────────────────────────────────────
/**
 * 用 POST + SSE 连接后端流式端点。
 * @param {string} path   API 路径
 * @param {object} body   请求体
 * @param {function} onEvent  每条事件回调 (event: object) => void
 * @param {function} onDone   完成回调
 * @param {function} onError  错误回调
 */
export function postSSE(path, body, onEvent, onDone, onError) {
    fetch(`${BASE_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    }).then(response => {
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        function read() {
            reader.read().then(({ done, value }) => {
                if (done) { onDone && onDone(); return }
                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop()
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const event = JSON.parse(line.slice(6))
                            onEvent(event)
                            if (event.type === 'done') { onDone && onDone(event); return }
                            if (event.type === 'error') { onError && onError(event.error); return }
                        } catch (e) { }
                    }
                }
                read()
            }).catch(e => onError && onError(e.message))
        }
        read()
    }).catch(e => onError && onError(e.message))
}

// ── API 方法封装 ──────────────────────────────────────────
export const dataPrepAPI = {
    getVideoInfo: (video_path) => api.post('/api/data-prep/video-info', { video_path }),
    extractFrames: (params, onEvent, onDone, onError) =>
        postSSE('/api/data-prep/extract-frames', params, onEvent, onDone, onError),
    scanImages: (params, onEvent, onDone, onError) =>
        postSSE('/api/data-prep/scan-images', params, onEvent, onDone, onError),
    deleteImages: (paths) => api.post('/api/data-prep/delete-images', { paths }),
    renamePreview: (params) => api.post('/api/data-prep/rename-preview', params),
    renameExecute: (entries) => api.post('/api/data-prep/rename-execute', { entries }),
}

export const datasetAPI = {
    load: (root_dir) => api.post('/api/dataset/load', { root_dir }),
    sanityCheck: (root_dir, onEvent, onDone, onError) =>
        postSSE('/api/dataset/sanity-check', { root_dir }, onEvent, onDone, onError),
    fixIssues: (issues) => api.post('/api/dataset/fix-issues', { issues }),
    getImageList: (root_dir) => api.post('/api/dataset/image-list', { root_dir }),
    getLabel: (img_path, root_dir) =>
        api.get(`/api/dataset/label?img_path=${encodeURIComponent(img_path)}&root_dir=${encodeURIComponent(root_dir)}`),
    getImage: (path) =>
        api.get(`/api/dataset/image?path=${encodeURIComponent(path)}`),
    analyze: (root_dir) => api.post('/api/dataset/analyze', { root_dir }),
    split: (params, onEvent, onDone, onError) =>
        postSSE('/api/dataset/split', params, onEvent, onDone, onError),
}

export const exportAPI = {
    /** 扫描项目目录下所有 .pt 权重文件 */
    scanWeights: (project_dir) => api.post('/api/export/scan-weights', { project_dir }),
    /** SSE 流式执行 ONNX 导出 */
    exportModel: (params, onEvent, onDone, onError) =>
        postSSE('/api/export/export', params, onEvent, onDone, onError),
}

