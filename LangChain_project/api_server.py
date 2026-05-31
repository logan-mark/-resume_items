from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import time
import json


from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agent_core import build_agent, get_all_thread_ids

# ==========================================
# 🛡️ 核心安全组件
# ==========================================
class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_fill) * self.fill_rate)
        self.last_fill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

global_rate_limiter = TokenBucket(capacity=10, fill_rate=2.0)

SECRET_API_KEY = "sk-my-super-secret-key-2026"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_security(api_key: str = Security(api_key_header)):
    if not global_rate_limiter.consume():
        raise HTTPException(status_code=429, detail="API 调用过于频繁 (Rate Limit Exceeded)")
    if api_key != SECRET_API_KEY:
        raise HTTPException(status_code=401, detail="无效或缺失的 API Key (Unauthorized)")
    return api_key

# ==========================================
# 系统生命周期与 API 模型
# ==========================================
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    print("⏳ [系统启动] 初始化模型与数据库...")
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
        # 【关键修复】确保首次运行时创建对应的数据库表！
        await memory.setup()
        agent = build_agent(memory)
        print("✅ [系统就绪] AI 服务已上线！")
        yield

app = FastAPI(title="AI 深度研究员 API", lifespan=lifespan)

class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ==========================================
# 🔒 核心路由网关
# ==========================================
@app.post("/api/v1/chat", dependencies=[Depends(verify_security)])
async def chat_endpoint(request: ChatRequest):
    """终极裸流接口：没有任何包装的纯净文字字节流"""
    config = {"configurable": {"thread_id": request.thread_id}}

    async def generate():
        try:
            # 先强行推一个空格，冲开所有的网络缓冲阀门！
            yield b" "

            async for msg, metadata in agent.astream({"messages": [("user", request.message)]}, config=config,
                                                     stream_mode="messages"):
                content = getattr(msg, "content", "")

                # 兼容多模态返回结构
                if isinstance(content, list):
                    content = "".join([c.get("text", "") for c in content if isinstance(c, dict)])

                # 只要有字，立刻编码成 utf-8 字节并喷射出去！
                if isinstance(content, str) and content:
                    yield content.encode("utf-8")

        except Exception as e:
            yield f"\n\n[后端报错: {str(e)}]".encode("utf-8")

    # 注意：media_type 必须是 text/plain，告诉网络“这是纯文本，别等格式，直接流！”
    return StreamingResponse(generate(), media_type="text/plain")
@app.get("/api/v1/history/{thread_id}", dependencies=[Depends(verify_security)])
async def get_history(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await agent.aget_state(config)

        if not state.values or "messages" not in state.values:
            return {"status": "success", "messages": []}

        formatted_messages = []
        for msg in state.values["messages"]:
            if msg.type in ["human", "ai"]:
                content = msg.content
                if isinstance(content, str) and content.strip():
                    role = "user" if msg.type == "human" else "assistant"
                    formatted_messages.append({"role": role, "content": content})

        return {"status": "success", "messages": formatted_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)