/**
 * inference.js — 推理测试模块 API 封装
 */
import axios from 'axios'

const BASE = 'http://127.0.0.1:8765/inference'

/**
 * 获取模型加载状态
 */
export async function getStatus() {
  const { data } = await axios.get(`${BASE}/status`)
  return data
}

/**
 * 加载模型（传入服务器本地绝对路径）
 * @param {string} modelPath - 模型文件绝对路径
 */
export async function loadModel(modelPath) {
  const { data } = await axios.post(`${BASE}/load`, { model_path: modelPath })
  return data
}

/**
 * 对单张图像进行推理
 * @param {string} imageB64 - base64 编码的图像（含或不含 data URI 头均可）
 * @param {number} confThreshold - 置信度阈值
 * @param {number} iouThreshold - IoU/NMS 阈值
 */
export async function inferImage(imageB64, confThreshold = 0.25, iouThreshold = 0.45) {
  const { data } = await axios.post(`${BASE}/image`, {
    image_b64: imageB64,
    conf_threshold: confThreshold,
    iou_threshold: iouThreshold,
  })
  return data
}
