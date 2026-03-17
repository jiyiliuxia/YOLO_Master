/**
 * debounce.js — 防抖工具函数
 */

/**
 * 创建防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟毫秒数
 */
export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}
