import json
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from pydantic import BaseModel

from app.core.agent.orchestrator import _get_llm, SYSTEM_PROMPT
from app.api.knowledge import get_doc_content

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY = 20
_conversations: dict[str, list[BaseMessage]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str = "default"
    filename: str | None = None
    enable_search: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    intent: str
    plan: list[dict] | None = None


async def _build_messages(req: ChatRequest, cid: str) -> list:
    msg_text = req.message
    if req.filename:
        doc = get_doc_content(req.filename, query=req.message)
        if doc["content"]:
            ctx = f"文件「{req.filename}」（共{doc.get('total_chunks', '?')}段，已匹配{doc.get('chunks_used', '?')}段最相关内容）"
            msg_text = f"{ctx}\n\n{doc['content']}\n\n用户提问：{req.message}"

    if req.enable_search:
        try:
            from app.api.tools import _do_search
            sr = await _do_search(req.message, 5)
            if sr and sr.status == "ok" and sr.results:
                lines = [f"- [{r.title}]({r.url}): {r.snippet}" for r in sr.results]
                msg_text = "以下是最新网络搜索结果，请基于这些信息回答用户问题：\n\n" + "\n".join(lines) + f"\n\n用户提问：{req.message}"
        except Exception:
            pass

    user_msg = HumanMessage(content=msg_text)
    history = _conversations.get(cid, [])
    history.append(user_msg)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    _conversations[cid] = history
    return [SystemMessage(content=SYSTEM_PROMPT)] + history


@router.post("/send")
async def send_message(req: ChatRequest) -> ChatResponse:
    conversation_id = req.conversation_id or str(uuid.uuid4())
    messages = await _build_messages(req, conversation_id)
    llm = _get_llm(streaming=False)
    response = await llm.ainvoke(messages)
    _conversations[conversation_id].append(AIMessage(content=response.content))
    return ChatResponse(
        conversation_id=conversation_id,
        message=response.content,
        intent="chat",
    )


@router.post("/stream")
async def stream_message(req: ChatRequest):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    messages = await _build_messages(req, conversation_id)
    llm = _get_llm(streaming=True)

    async def event_generator():
        full = ""
        async for chunk in llm.astream(messages):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                full += token
                yield f"data: {json.dumps({'type': 'message', 'content': token}, ensure_ascii=False)}\n\n"
        _conversations[conversation_id].append(AIMessage(content=full))
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
