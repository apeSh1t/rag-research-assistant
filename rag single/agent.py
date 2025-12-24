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
        
        Args:
            user_input: 用户问题描述
            
        Returns:
            包含详细步骤的解决方案计划
        """
        try:
            # 使用Agent执行器处理用户输入
            result = self.agent_executor.invoke({
                "input": f"请为以下问题制定详细的解决方案计划：\n\n{user_input}"
            })
            return result
            
                
        except Exception as e:
            return {
                "success": False,
                "error": f"error: {e}",
                "raw_response": ""
            }
    
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