"""
File Upload API Route - 简化版
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
import shutil
from pathlib import Path

router = APIRouter()

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档 - 简化版，只保存文件"""
    try:
        # 生成唯一文件名
        paper_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        file_path = UPLOAD_DIR / f"{paper_id}{file_ext}"
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "data": {
                "paperId": paper_id,
                "title": file.filename,
                "abstract": "File uploaded"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
