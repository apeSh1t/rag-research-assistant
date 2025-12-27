"""
FastAPI Backend for RAG Research Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import upload, search, retrieve, parse, agent
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置 Hugging Face 镜像，解决国内下载模型失败的问题
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

app = FastAPI(
    title="RAG Research Assistant API",
    description="Backend API for document upload, search, retrieval and intelligent Q&A",
    version="1.0.0 (MVP)"
)

# 挂载静态文件目录，用于预览 PDF
UPLOAD_DIR = Path(__file__).parent.parent / "rag single" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境下允许所有来源，解决网络连接错误
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(retrieve.router, prefix="/api", tags=["Retrieve"])
app.include_router(parse.router, prefix="/api", tags=["Parse"])
app.include_router(agent.router, prefix="/api", tags=["Agent"])


@app.get("/")
async def root():
    return {
        "message": "RAG Research Assistant API",
        "version": "1.0.0 (MVP)",
        "status": "running",
        "features": {
            "document_upload": True,
            "basic_search": True,
            "intelligent_qa": True
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # 关闭自动重载，避免多进程争用向量库文件
    )
