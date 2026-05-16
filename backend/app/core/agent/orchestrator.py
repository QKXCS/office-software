from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.agent.state import AgentState

_graph = None


def _get_llm(streaming: bool = True):
    provider = settings.default_llm_provider

    if provider == "openai":
        return ChatOpenAI(
            model=settings.default_llm_model,
            api_key=settings.openai_api_key,
            streaming=streaming,
        )
    if provider == "doubao":
        return ChatOpenAI(
            model=settings.default_llm_model,
            api_key=settings.doubao_api_key,
            base_url=settings.doubao_base_url,
            streaming=streaming,
        )
    return ChatAnthropic(
        model=settings.default_llm_model or "claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        streaming=streaming,
    )


SYSTEM_PROMPT = """你是一个智能办公助手，帮助用户高效完成各类办公任务。

你的能力包括：
- 文档处理：总结、翻译、问答、对比
- 邮件管理：分类、摘要、起草回复
- 日程管理：创建日程、查找空闲时间
- 会议纪要：转录总结、提取待办
- 知识检索：搜索知识库，精准回答
- 数据分析：处理表格数据、生成图表
- 网络搜索：获取最新信息

请用中文回复，简洁专业。遇到不确定的信息，诚实地告知用户。"""


async def smart_respond(state: AgentState) -> dict:
    llm = _get_llm()
    messages = state["messages"]
    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    system = SystemMessage(content=SYSTEM_PROMPT)
    response = await llm.ainvoke([system, HumanMessage(content=content)])
    return {"messages": [response], "final_response": response.content, "intent": "chat"}


def build_agent_graph() -> StateGraph:
    global _graph
    if _graph is not None:
        return _graph

    graph = StateGraph(AgentState)
    graph.add_node("smart_respond", smart_respond)
    graph.set_entry_point("smart_respond")
    graph.add_edge("smart_respond", END)

    _graph = graph.compile()
    return _graph
