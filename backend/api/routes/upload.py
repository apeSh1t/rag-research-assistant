"""
File Upload API Route - 上传并索引到知识库
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import hashlib
import shutil
import sys
from pathlib import Path

router = APIRouter()

# 添加 rag single 路径到 Python path
RAG_DIR = Path(__file__).parent.parent.parent.parent / "rag single"
if str(RAG_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DIR))

# 延迟导入，确保路径已添加
from knowledge_base.kb import KnowledgeBase  # type: ignore

# 创建上传目录 - 放在 rag single 目录下
UPLOAD_DIR = RAG_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 初始化知识库
kb = KnowledgeBase(kb_dir=str(RAG_DIR / "knowledge_base"), use_english=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档并添加到RAG知识库（带去重）"""
    try:
        file_ext = os.path.splitext(file.filename or "")[1]
        
        # 1. 读取文件内容并计算哈希值
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # 2. 检查是否已存在相同文件
        existing_file = None
        for existing in UPLOAD_DIR.glob(f"*{file_ext}"):
            with open(existing, "rb") as f:
                if hashlib.md5(f.read()).hexdigest() == file_hash:
                    existing_file = existing
                    break
        
        if existing_file:
            # 文件已存在，直接返回
            paper_id = existing_file.stem
            return {
                "status": "success",
                "message": "File already exists, skipped upload",
                "data": {
                    "paperId": paper_id,
                    "title": file.filename,
                    "abstract": "File already indexed",
                    "indexed": True,
                    "duplicate": True
                }
            }
        
        # 3. 新文件，使用哈希值作为文件名（更简洁）
        paper_id = file_hash
        file_path = UPLOAD_DIR / f"{paper_id}{file_ext}"
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 4. 添加到知识库（仅处理PDF）
        index_result = None
        if file_ext.lower() == '.pdf':
            index_result = kb.add_pdf_document(
                str(file_path), 
                title=file.filename
            )
        
        return {
            "status": "success",
            "message": "File uploaded and indexed successfully",
            "data": {
                "paperId": paper_id,
                "title": file.filename,
                "abstract": "File uploaded",
                "indexed": index_result.get("success", False) if index_result else False,
                "chunks": index_result.get("chunks", 0) if index_result else 0,
                "duplicate": False
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
