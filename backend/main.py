"""
main.py — YOLO-Studio FastAPI 后端入口
运行: uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import data_prep, dataset, inference, export

app = FastAPI(
    title="YOLO-Studio API",
    description="视觉模型工作站后端服务",
    version="0.3.0",
)

# 允许来自 Tauri WebView / 本地开发服务器的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境限定为 tauri://localhost
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_prep.router)
app.include_router(dataset.router)
app.include_router(inference.router)
app.include_router(export.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}


if __name__ == "__main__":
    import uvicorn
    # 打包后必须传 app 对象，不能用字符串 "main:app"（PyInstaller 无法动态导入）
    uvicorn.run(app, host="127.0.0.1", port=8765, reload=False)
