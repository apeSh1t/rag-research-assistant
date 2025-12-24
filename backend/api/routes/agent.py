"""
Agent API Route - 智能问答接口
集成 rag single 中的 Agent 系统，提供多步推理能力
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import json
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

router = APIRouter()

# 加载环境变量
load_dotenv()

# 添加 rag single 到路径
rag_path = Path(__file__).parent.parent.parent.parent / "rag single"
sys.path.insert(0, str(rag_path))

# 延迟导入，确保路径已添加
try:
    from knowledge_base.kb import KnowledgeBase
    from agent import Agent
except ImportError as e:
    print(f"⚠️ 警告：无法导入 Agent 模块: {e}")
    Agent = None
    KnowledgeBase = None


class AgentRequest(BaseModel):
    query: str
    context: Optional[List[Dict[str, str]]] = []


class AgentResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


# 全局 Agent 实例（懒加载）
_agent_instance = None


def get_agent():
    """获取或创建 Agent 实例"""
    global _agent_instance
    
    if _agent_instance is None:
        if Agent is None or KnowledgeBase is None:
            raise HTTPException(
                status_code=500, 
                detail="Agent 模块未正确加载，请检查 rag single 目录"
            )
        
        # 初始化知识库
        kb_dir = rag_path / "knowledge_base"
        kb = KnowledgeBase(str(kb_dir), use_english=True)
        
        # 获取 LLM 配置
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("LLM_MODEL", "qwen-max")
        base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="未配置 API Key，请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY"
            )
        
        # 创建 Agent 实例
        try:
            _agent_instance = Agent(
                knowledge_base=kb,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url
            )
                
            print(f"✅ Agent 初始化成功 (Model: {model_name})")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Agent 初始化失败: {str(e)}"
            )
    
    return _agent_instance


@router.post("/agent/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    """
    智能问答接口 - 使用 Agent 进行多步推理
    
    Args:
        request: 包含用户问题和对话上下文
        
    Returns:
        Agent 的推理结果和答案
    """
    try:
        agent = get_agent()
        
        # 构建完整的输入（包含上下文）
        full_input = request.query
        if request.context:
            context_str = "\n".join([
                f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
                for item in request.context
            ])
            full_input = f"对话历史:\n{context_str}\n\n当前问题: {request.query}"
        
        # 调用 Agent
        result = agent.run(full_input)
        
        # 格式化返回结果
        if isinstance(result, dict):
            # 处理 LangChain 的 intermediate_steps，将其转换为可序列化的格式
            reasoning_steps = []
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    step = {
                        "thought": getattr(action, "log", ""),
                        "tool": getattr(action, "tool", ""),
                        "tool_input": getattr(action, "tool_input", ""),
                        "observation": str(observation)
                    }
                    reasoning_steps.append(step)

            return AgentResponse(
                status="success",
                message="Agent 执行成功",
                data={
                    "answer": result.get("output", ""),
                    "reasoning": reasoning_steps
                }
            )
        else:
            # 如果返回的是字符串或其他格式
            return AgentResponse(
                status="success",
                message="Agent 执行成功",
                data={
                    "answer": str(result),
                    "reasoning": []
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()  # 在控制台打印完整错误堆栈
        raise HTTPException(
            status_code=500,
            detail=f"Agent 执行错误: {str(e)}"
        )


@router.post("/agent/chat_stream")
async def agent_chat_stream(request: AgentRequest):
    """
    流式智能问答接口 - 实时返回 Agent 的思考步骤
    """
    agent = get_agent()
    
    # 构建完整的输入
    full_input = request.query
    if request.context:
        context_str = "\n".join([
            f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
            for item in request.context
        ])
        full_input = f"对话历史:\n{context_str}\n\n当前问题: {request.query}"

    async def event_generator():
        try:
            async for event in agent.run_stream(full_input):
                # 将事件转换为 JSON 字符串并添加换行符，方便前端解析
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/agent/status")
async def agent_status():
    """检查 Agent 服务状态"""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "message": "Agent 服务运行正常",
            "model": os.getenv("LLM_MODEL", "qwen-max"),
            "agent_ready": agent is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Agent 服务异常: {str(e)}",
            "agent_ready": False
        }
