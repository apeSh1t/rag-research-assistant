"""
使用Agent架构，自主搜索知识库并生成详细解决方案
"""
import json
from typing import Dict, List, Any
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from knowledge_base.kb import KnowledgeBase


class Agent:
    """规划Agent：基于知识库和工具接口json schema，生成分步、结构化的解决方案计划"""
    
    def __init__(self, knowledge_base: KnowledgeBase, tools_schema_path: str = None, model_name: str = "qwen-max", api_key: str = None, base_url: str = None):
        self.kb = knowledge_base
        
        # 默认在当前文件所在目录查找 tools_schema.json
        if tools_schema_path is None:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            tools_schema_path = os.path.join(current_dir, "tools_schema.json")
            
        self.tools_schema = self._load_tools_schema(tools_schema_path)
        
        # 创建知识库搜索工具
        @tool
        def search_knowledge(query: str) -> str:
            """
            搜索知识库获取相关信息。
            """
            return self.kb.retrieve(query, k=3)
        

        self.tools = [search_knowledge]

        # 初始化LLM和Agent
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=api_key or "your-api-key-here",
            base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 设置规划Agent
        self._setup_planning_agent()
    
    def _load_tools_schema(self, schema_path: str) -> List[Dict]:
        """加载工具schema"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告：无法加载工具schema ({e})，将使用空schema")
            return []
    
    def _setup_planning_agent(self):
        """设置规划Agent"""   
        system_prompt = f"""你是solution planing专家。你的任务是分析用户问题，制定详细的分步解决方案计划。简单的问题可以直接用llm计算解决，复杂问题需要查询知识库并调用工具。

可用工具：
- search_knowledge: 查询知识库获取相关方法和原理


工作流程：
1. 遇到不懂的问题或概念 → 调用search_knowledge查询知识库
2. 搜不到时尝试分析问题改变query搜索问题，务必根据知识来决策，至少要搜到一次
3. 根据返回的信息判断，制定详细执行计划：
   - 如果知识库返回了方法描述 → 理解后发现能直接靠llm计算--添加llm_reasoning step; 如果依然不清楚，继续查询知识库
4. 根据工具或llm_reasoning的预期返回继续分析是否达到目的，下一步该做什么
5. 递归处理所有子问题直到能够完全解决用户问题，获得想要的结果
6. 输出前分析计划评估是否清楚每一步，是否解决用户问题，最终输出是否简单易懂，否则重复上面步骤
7. 当你得到最终结果时，请务必以 "Final Answer:" 开头输出最终答案。

请务必在思考过程中清晰地描述你的每一步行动，例如：“我将首先搜索关于...的知识”，“根据搜索结果，我发现...，接下来我将...”。

例子：
用户: "配制RGB(128,20,190)颜色"
→ search_knowledge("RGB颜色配制")
← 返回: 需要RGB→CMY、计算比例、多组分混合
→ search_knowledge("RGB转CMY")
← 返回: 公式C=255-R...
→ 添加直接计算步骤
→ 分析下一步"计算比例"
"""

        # 创建工具列表
        tools = self.tools
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # 创建Agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # 创建Agent执行器
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
       
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        根据用户输入创建详细的解决方案计划
        使用Agent架构，让LLM自主决定何时搜索知识库
        """
        try:
            # 使用Agent执行器处理用户输入
            result = self.agent_executor.invoke({
                "input": f"请为以下问题制定详细的解决方案计划：\n\n{user_input}"
            })
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_stream(self, user_input: str):
        """
        异步流式输出 Agent 的思考过程和结果
        """
        # 保持与 run 方法一致的 prompt 构建
        full_input = f"请为以下问题制定详细的解决方案计划：\n\n{user_input}"
        
        try:
            # 记录完整的思考过程和最终答案
            buffer = ""
            final_answer_started = False
            action_started = False
            
            async for event in self.agent_executor.astream_events(
                {"input": full_input},
                version="v1"
            ):
                kind = event["event"]
                
                # 捕获工具调用开始
                if kind == "on_tool_start":
                    # 如果有未发送的缓冲内容（通常是思考），先发送
                    if buffer.strip() and not action_started:
                        # 清理 "Thought:" 前缀
                        content_to_send = buffer.replace("Thought:", "").replace("Thought", "").strip()
                        if content_to_send:
                            yield {"type": "thought_chunk", "content": content_to_send}
                    buffer = ""
                    
                    action = event['data'].get('input')
                    # 兼容不同版本的 LangChain
                    if hasattr(action, 'tool'):
                        tool_name = action.tool
                        tool_input = action.tool_input
                    else:
                        tool_name = event['name']
                        tool_input = event['data'].get('input')
                        
                    yield {
                        "type": "thought",
                        "content": f"正在使用 {tool_name}...",
                        "tool": tool_name,
                        "tool_input": tool_input
                    }
                
                # 捕获模型输出的 Token (实现打字机效果)
                elif kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if not content:
                        continue
                    
                    # 1. 如果已经进入 Final Answer 阶段，直接作为回答发送
                    if final_answer_started:
                        yield {"type": "answer_chunk", "content": content}
                        continue

                    # 2. 如果已经进入 Action 阶段（正在生成工具调用代码），则不发送给前端（隐藏 Action 声明）
                    if action_started:
                        continue

                    # 3. 缓冲内容以进行检测
                    buffer += content
                    
                    # 检测 Final Answer
                    if "Final Answer" in buffer:
                        final_answer_started = True
                        # 找到分割点
                        split_marker = "Final Answer:" if "Final Answer:" in buffer else "Final Answer"
                        parts = buffer.split(split_marker, 1)
                        
                        # 分割点之前的内容属于思考
                        thought_content = parts[0].replace("Thought:", "").replace("Thought", "").strip()
                        if thought_content:
                            yield {"type": "thought_chunk", "content": thought_content}
                        
                        # 分割点之后的内容属于回答
                        if len(parts) > 1 and parts[1]:
                            yield {"type": "answer_chunk", "content": parts[1]}
                        
                        buffer = "" # 清空缓冲
                        continue

                    # 检测 Action (隐藏 Action: ... 及其后的内容直到工具调用)
                    if "Action" in buffer:
                        # 找到 Action 的位置
                        action_index = buffer.find("Action")
                        # Action 之前的内容是思考
                        thought_content = buffer[:action_index].replace("Thought:", "").replace("Thought", "").strip()
                        if thought_content:
                            yield {"type": "thought_chunk", "content": thought_content}
                        
                        action_started = True
                        buffer = "" # 清空缓冲，后续的 Action 内容将被忽略
                        continue

                    # 如果缓冲区过大且没有特殊标记，则将前面的内容作为思考发送
                    # 保留最后一部分以防标记被切断 (例如 "Final A" 或 "Act")
                    if len(buffer) > 20:
                        to_send = buffer[:-15]
                        buffer = buffer[-15:]
                        # 只有当 to_send 不仅仅是 "Thought" 时才发送，避免重复
                        clean_send = to_send.replace("Thought:", "").replace("Thought", "").strip()
                        if clean_send:
                            yield {"type": "thought_chunk", "content": clean_send}
                
                # 捕获工具执行结束
                elif kind == "on_tool_end":
                    action_started = False # Action 结束，恢复正常流式输出（通常接下来是 Observation）
                    buffer = "" # 确保缓冲清空
                        
                    output = event['data'].get('output')
                    yield {
                        "type": "observation",
                        "content": str(output) if output else "无结果",
                        "tool": event['name']
                    }
                
                # 捕获最终输出
                elif kind == "on_agent_finish":
                    # 确保所有缓冲都已处理
                    if buffer and not final_answer_started and not action_started:
                         # 如果缓冲区包含 Final Answer，说明它是回答的一部分，不要作为思考发送
                         if "Final Answer" in buffer:
                             pass
                         else:
                             clean_buffer = buffer.replace("Thought:", "").replace("Thought", "").strip()
                             if clean_buffer:
                                yield {"type": "thought_chunk", "content": clean_buffer}
                    
                    output = event["data"]["output"]
                    # 清理 Final Answer 标记，防止重复
                    clean_output = output.replace("Final Answer:", "").replace("Final Answer", "").strip()
                    yield {
                        "type": "final_answer",
                        "content": clean_output
                    }
        except Exception as e:
            yield {"type": "error", "content": str(e)}
    
def test_agent():
    """测试规划Agent"""
    # 初始化知识库和规划Agent
    kb = KnowledgeBase("knowledge_base")
    agent = Agent(kb)
    
    # 测试用例
    test_cases = [
        {
            "name": "酒精稀释测试",
            "input": "我需要将95%的酒精稀释到70%"
        },
        {
            "name": "多组分混合测试", 
            "input": "我需要制备含有0.15浓度NaCl和0.25浓度葡萄糖的混合液。现在有纯水、30%NaCl溶液和60%葡萄糖溶液"
        },
        {
            "name": "颜色配制测试",
            "input": "配制RGB(150,20,190)的颜色，k=0.6"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🎯 规划测试 {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"问题: {test_case['input']}")
        print("-" * 80)
        
        # 调用
        result = agent.run(test_case['input'])
        print(result)
        

        
        print("-" * 80)
        input("\n按Enter继续下一个测试...")


if __name__ == "__main__":
    test_agent()