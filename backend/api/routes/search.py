"""
Search API Route - 简化版
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

router = APIRouter()

# 添加 rag single 到路径
rag_path = Path(__file__).parent.parent.parent.parent / "rag single"
sys.path.insert(0, str(rag_path))


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search_documents(request: SearchRequest):
    """使用 rag single 的知识库搜索"""
    try:
        from knowledge_base.kb import KnowledgeBase
        
        # 初始化知识库
        kb_dir = rag_path / "knowledge_base"
        kb = KnowledgeBase(str(kb_dir), use_english=True)
        
        # 搜索
        results_text = kb.retrieve(request.query, k=5)
        
        # 简单解析结果
        results = []
        if results_text and "未找到" not in results_text:
            sections = results_text.split('\n\n')
            for section in sections[:5]:
                if section.strip():
                    results.append({
                        "section": "Document",
                        "content": section.strip()[:200],  # 限制长度
                        "score": 0.0
                    })
        
        return {
            "status": "success",
            "message": "Search completed",
            "data": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "data": []
        }
