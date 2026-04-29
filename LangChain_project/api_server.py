from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import time

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agent_core import build_agent
from agent_core import build_agent, get_all_thread_ids

# ==========================================
# 🛡️ 核心安全组件 1：纯手工令牌桶限流器
# ==========================================
class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity  # 桶的最大容量（允许的突发并发数）
        self.fill_rate = fill_rate  # 每秒补充的令牌数
        self.tokens = capacity  # 初始状态桶是满的
        self.last_fill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_fill

        # 计算这段时间内又滴进来了多少令牌，但不能超过桶的容量
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
        self.last_fill = now

        # 判断剩下的令牌够不够消耗
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


# 实例化全局限流器：最多攒 5 个令牌，每秒回复 0.5 个（即 2 秒允许访问 1 次）
# (在真实的商业系统中，这个桶通常会存在 Redis 里，并根据每个用户的 IP 独立计算)
global_rate_limiter = TokenBucket(capacity=5, fill_rate=0.5)

# ==========================================
# 🛡️ 核心安全组件 2：API Key 鉴权
# ==========================================

SECRET_API_KEY = "sk-my-super-secret-key-2026"

# 告诉 FastAPI，我们要从 HTTP 请求的 Header 里找一个叫 "X-API-Key" 的字段
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_security(api_key: str = Security(api_key_header)):
    """这是一个安全校验拦截器，所有进来的请求必须先过这一关"""

    # 1. 先查水表（限流检查）
    if not global_rate_limiter.consume():
        print("🚨 拦截：请求过于频繁！触发限流。")
        raise HTTPException(status_code=429, detail="API 调用过于频繁，请稍后再试 (Rate Limit Exceeded)")

    # 2. 对暗号（API Key 检查）
    if api_key != SECRET_API_KEY:
        print(f"🚨 拦截：有人尝试使用错误的密钥闯入！提供的值: {api_key}")
        raise HTTPException(status_code=401, detail="无效或缺失的 API Key (Unauthorized)")

    return api_key


# ==========================================
# 原有的生命周期与模型初始化 (保持不变)
# ==========================================
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    print("⏳ [系统启动] 正在建立异步数据库连接与加载大模型...")
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
        agent = build_agent(memory)
        print("✅ [系统就绪] AI 深度研究员已上线，安全防盗门已锁闭！")
        yield
    print("🛑 [系统关闭] 正在安全断开连接...")


app = FastAPI(title="AI 深度研究员 API (安全版)", lifespan=lifespan)


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ChatResponse(BaseModel):
    status: str
    reply: str


# ==========================================
# 🔒 路由网关改造：注入安全拦截器
# ==========================================
# 注意这里增加了 Depends(verify_security)
@app.post("/api/v1/chat", response_model=ChatResponse, dependencies=[Depends(verify_security)])
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    try:
        result = await agent.ainvoke({"messages": [("user", request.message)]}, config=config)
        return ChatResponse(status="success", reply=result["messages"][-1].content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/v1/threads", dependencies=[Depends(verify_security)])
async def get_threads():
    """获取所有历史会话 ID"""
    try:
        # 去 sqlite 数据库里把所有存活的 thread_id 捞出来
        threads = get_all_thread_ids("checkpoints.db")
        return {"status": "success", "threads": threads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/history/{thread_id}", dependencies=[Depends(verify_security)])
async def get_history(thread_id: str):
    """获取特定会话的漫长历史记忆"""
    try:
        # 组装钥匙
        config = {"configurable": {"thread_id": thread_id}}

        # 🌟 核心：从 LangGraph 的 SQLite 检查点中提取状态快照
        state = await agent.aget_state(config)

        # 如果是个空会话，直接返回空列表
        if not state.values or "messages" not in state.values:
            return {"status": "success", "messages": []}

        formatted_messages = []
        for msg in state.values["messages"]:
            # 我们只提取人类(human)的提问和大模型(ai)的文本回答
            # 自动过滤掉 LangGraph 内部调用工具时的啰嗦日志
            if msg.type in ["human", "ai"]:
                content = msg.content
                if isinstance(content, str) and content.strip():
                    role = "user" if msg.type == "human" else "assistant"
                    formatted_messages.append({"role": role, "content": content})

        return {"status": "success", "messages": formatted_messages}
    except Exception as e:
        print(f"🚨 提取记忆报错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)