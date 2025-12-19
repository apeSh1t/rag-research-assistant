"""
Document Retrieval API Route - 简化版
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/retrieve")
async def retrieve_document(paperId: str):
    """占位符 - 如果前端不用可以删除"""
    return {
        "status": "success",
        "message": "Retrieve endpoint",
        "data": {"paperId": paperId}
    }
