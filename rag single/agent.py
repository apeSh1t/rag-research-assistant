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
            Search the knowledge base for relevant information.
            """
            # Use structured retrieval to surface chunk_info with hierarchy
            results = self.kb.retrieve_structured(query, k=5)
            if not results:
                return "No hits"

            lines = []
            for item in results:
                lines.append(
                    f"[Rank {item.get('rank')}] ID={item.get('id')} | Page={item.get('page_no')} | "
                    f"Category={item.get('category')} | Score={item.get('score'):.4f} | "
                    f"Headings={item.get('headings')} | Caption={item.get('caption')} | Source={item.get('source')}\n"
                    f"Text: {item.get('text')}\nContext: {item.get('context')}"
                )
            return "\n\n".join(lines)
        

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
        system_prompt = f"""You are a solution planning expert. Your task is to analyze user problems and formulate detailed step-by-step solution plans. Simple problems can be solved directly by LLM calculation, while complex problems require querying the knowledge base and calling tools.

IMPORTANT: You must ALWAYS output in ENGLISH, regardless of the user's input language.

Available Tools:
- search_knowledge: Query the knowledge base for relevant methods and principles.

Workflow:
1. Encountering unknown problems or concepts → Call search_knowledge to query the knowledge base.
2. If search yields no results, try analyzing the problem and changing the query to search again. You must make decisions based on knowledge, and search at least once.
3. Based on the returned information, formulate a detailed execution plan:
   - If the knowledge base returns a method description → Understand it and if it can be solved directly by LLM calculation -- add an llm_reasoning step; if still unclear, continue querying the knowledge base.
4. Based on the expected return of the tool or llm_reasoning, continue to analyze whether the goal is achieved and what to do next.
5. Recursively handle all sub-problems until the user's problem can be completely solved and the desired result is obtained.
6. Before outputting, analyze the plan to assess if every step is clear, if it solves the user's problem, and if the final output is simple and easy to understand. Otherwise, repeat the steps above.
7. IMPORTANT: While you think this answer can output to user, you MUST repeat the answer again and start repeating with "Final Answer:".

Please clearly describe your every action during the thinking process, for example: "I will first search for knowledge about...", "Based on the search results, I found..., next I will...".

Example:
User: "Prepare RGB(128,20,190) color"
→ search_knowledge("RGB color preparation")
← Returns: Needs RGB→CMY, ratio calculation, multi-component mixing
→ search_knowledge("RGB to CMY")
← Returns: Formula C=255-R...
→ Add direct calculation step
→ Analyze next step "Calculate ratio"
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
                "input": f"Please formulate a detailed solution plan for the following problem:\n\n{user_input}"
            })
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_stream(self, user_input: str):
        """
        异步流式输出 Agent 的思考过程和结果
        """
        # 保持与 run 方法一致的 prompt 构建
        full_input = f"Please formulate a detailed solution plan for the following problem:\n\n{user_input}"
        
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
                        "content": f"Using {tool_name}...",
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
                        # Content before Action is thought
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
                        "content": str(output) if output else "No result",
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
            "name": "Alcohol Dilution Test",
            "input": "I need to dilute 95% alcohol to 70%"
        },
        {
            "name": "Multi-component Mixing Test", 
            "input": "I need to prepare a mixture containing 0.15 concentration NaCl and 0.25 concentration glucose. I have pure water, 30% NaCl solution, and 60% glucose solution."
        },
        {
            "name": "Color Preparation Test",
            "input": "Prepare RGB(150,20,190) color, k=0.6"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🎯 Planning Test {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"Problem: {test_case['input']}")
        print("-" * 80)
        
        # Call
        result = agent.run(test_case['input'])
        print(result)
        print("-" * 80)
        input("\n按Enter继续下一个测试...")


if __name__ == "__main__":
    test_agent()