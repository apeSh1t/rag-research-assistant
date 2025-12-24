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
        print(f"\n[UPLOAD] 开始处理文件: {file.filename}")
        file_ext = os.path.splitext(file.filename or "")[1]
        
        # 1. 读取文件内容并计算哈希值
        print(f"[UPLOAD] 正在读取文件内容...")
        file_content = await file.read()
        file_size = len(file_content)
        print(f"[UPLOAD] 文件读取完成, 大小: {file_size / 1024:.2f} KB")
        
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # 2. 检查是否已存在相同文件
        existing_file = None
        for existing in UPLOAD_DIR.glob(f"*{file_ext}"):
            with open(existing, "rb") as f:
                if hashlib.md5(f.read()).hexdigest() == file_hash:
                    existing_file = existing
                    break
        
        if existing_file:
            print(f"[UPLOAD] 检测到重复文件: {existing_file.name}, 跳过上传")
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
        
        print(f"[UPLOAD] 正在保存文件到: {file_path}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 4. 添加到知识库 - 使用线程池避免阻塞
        print(f"[UPLOAD] 开始进入索引阶段 (Embedding)... 这可能需要一些时间")
        try:
            index_result = await run_in_threadpool(kb.add_document, str(file_path), file.filename)
            if index_result.get("success"):
                print(f"[UPLOAD] 索引成功! 产生了 {index_result.get('chunks')} 个知识片段")
            else:
                print(f"[UPLOAD] 索引失败: {index_result.get('message')}")
        except Exception as e:
            print(f"[UPLOAD] 索引过程发生异常: {str(e)}")
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
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

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
            raise HTTPException(status_code=404, detail="文件不存在")
            
        # 2. 从向量库删除 (使用文件名作为 title 匹配)
        kb.delete_document(filename)
        
        # 3. 删除物理文件
        os.remove(target_file)
        
        return {"status": "success", "message": f"已删除文档: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")