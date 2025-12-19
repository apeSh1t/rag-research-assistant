"""
FastAPI Backend for RAG Research Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import upload, search, retrieve, parse
import uvicorn

app = FastAPI(
    title="RAG Research Assistant API",
    description="Backend API for document upload, search, and retrieval",
    version="1.0.0"
)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(retrieve.router, prefix="/api", tags=["Retrieve"])
app.include_router(parse.router, prefix="/api", tags=["Parse"])


@app.get("/")
async def root():
    return {
        "message": "RAG Research Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式自动重载
    )
