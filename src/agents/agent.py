"""
配电网韧性评估智能体

该智能体能够自动执行配电网韧性评估的完整流程，包括：
1. 场景阶段分类
2. 滚动拓扑重构
3. 移动储能参与求解（MESS 协同调度）
"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入工具
from tools.resilience_assessment_tool import run_resilience_assessment, check_data_status

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    result = add_messages(old, new)
    # 确保返回列表，并进行切片
    if isinstance(result, list):
        return result[-MAX_MESSAGES:]
    else:
        # 如果返回的是单个消息，包装成列表
        return [result][-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """
    构建配电网韧性评估智能体
    
    该智能体具有以下能力：
    1. 接收电力系统数据和场景数据
    2. 自动按顺序执行场景阶段分类、拓扑重构、MESS 协同调度
    3. 返回评估结果和输出文件
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 定义可用工具
    tools = [
        run_resilience_assessment,
        check_data_status,
    ]
    
    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
