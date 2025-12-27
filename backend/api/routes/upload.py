"""
File Upload API Route - 上传并索引到知识库
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import hashlib
import shutil
import sys
from pathlib import Path
from starlette.concurrency import run_in_threadpool

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
        print(f"\n[UPLOAD] Start processing file: {file.filename}")
        file_ext = os.path.splitext(file.filename or "")[1]
        
        # 1. 读取文件内容并计算哈希值
        print(f"[UPLOAD] Reading file content...")
        file_content = await file.read()
        file_size = len(file_content)
        print(f"[UPLOAD] File read complete, size: {file_size / 1024:.2f} KB")
        
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # 2. 检查是否已存在相同文件
        existing_file = None
        for existing in UPLOAD_DIR.glob(f"*{file_ext}"):
            with open(existing, "rb") as f:
                if hashlib.md5(f.read()).hexdigest() == file_hash:
                    existing_file = existing
                    break
        
        if existing_file:
            print(f"[UPLOAD] Duplicate file detected: {existing_file.name}, skipping upload")
            return {
                "status": "success",
                "message": "File already exists, skipped upload",
                "data": {
                    "paperId": existing_file.stem,
                    "title": existing_file.name,
                    "abstract": "File already indexed",
                    "indexed": True,
                    "duplicate": True
                }
            }
        
        # 3. 使用原始文件名保存
        file_path = UPLOAD_DIR / file.filename
        paper_id = Path(file.filename).stem
        
        print(f"[UPLOAD] Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 4. 添加到知识库 - 使用线程池避免阻塞
        print(f"[UPLOAD] Starting indexing phase (Embedding)... This may take some time")
        try:
            index_result = await run_in_threadpool(kb.add_document, str(file_path), file.filename)
            if index_result.get("success"):
                print(f"[UPLOAD] Indexing successful! Generated {index_result.get('chunks')} knowledge chunks")
            else:
                print(f"[UPLOAD] Indexing failed: {index_result.get('message')}")
        except Exception as e:
            print(f"[UPLOAD] Exception during indexing: {str(e)}")
            index_result = {"success": False}
        
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
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents")
async def list_documents():
    """获取已上传文档列表"""
    docs = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            docs.append({
                "paperId": file_path.name,  # 使用完整文件名作为 ID
                "title": file_path.name,
                "size": os.path.getsize(file_path),
                "type": file_path.suffix.lower()
            })
    return {"status": "success", "data": docs}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """删除文档及其向量索引"""
    try:
        # 1. 检查文件是否存在
        target_file = UPLOAD_DIR / filename
        
        if not target_file.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        # 2. 从向量库删除 (使用文件名作为 title 匹配)
        kb.delete_document(filename)
        
        # 3. 删除物理文件
        os.remove(target_file)
        
        return {"status": "success", "message": f"Document deleted: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")