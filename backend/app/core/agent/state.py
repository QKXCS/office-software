from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class TaskStep(TypedDict):
    id: int
    description: str
    tool_name: str | None
    tool_args: dict | None
    status: str
    result: str | None


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    intent: str
    plan: list[dict] | None
    current_step: int
    tool_results: list[dict]
    final_response: str | None
    memory_context: str
    error_count: int
