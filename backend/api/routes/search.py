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
        # 修改 kb.retrieve 以返回原始结果或更易解析的格式
        # 这里我们直接调用 vector_store 进行搜索以获取更多元数据
        if kb.vector_store:
            results_with_scores = kb.vector_store.similarity_search_with_score(request.query, k=5)
            
            formatted_results = []
            for doc, score in results_with_scores:
                if score < 1.2: # 稍微放宽一点阈值
                    formatted_results.append({
                        "section": doc.metadata.get("title", "Unknown Document"),
                        "content": doc.page_content,
                        "score": float(score),
                        "source": doc.metadata.get("source", "Unknown Source")
                    })
            
            return {
                "status": "success",
                "message": f"Found {len(formatted_results)} results",
                "data": formatted_results
            }
        
        return {
            "status": "success",
            "message": "Knowledge base not loaded",
            "data": []
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "data": []
        }
