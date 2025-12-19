"""
Document Parsing API Route - 简化版
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ParseRequest(BaseModel):
    fileId: str


@router.post("/parse")
async def parse_document(request: ParseRequest):
    """解析文档，返回分段内容"""
    return {
        "status": "success",
        "message": "Document parsed successfully",
        "data": {
            "sections": [
                {
                    "section": "Introduction",
                    "content": "This is the introduction section."
                },
                {
                    "section": "Methods", 
                    "content": "This is the methods section."
                }
            ]
        }
    }
