"""
main.py — YOLO-Studio FastAPI 后端入口
运行: uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import data_prep, dataset

app = FastAPI(
    title="YOLO-Studio API",
    description="视觉模型工作站后端服务",
    version="0.2.0",
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8765, reload=False)
