import os
import sqlite3
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
# 如果未来需要加回联网搜索，可以取消注释下面的导入
# from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

# ==========================================
# 1. 数据库辅助函数
# ==========================================
def get_all_thread_ids(db_path="checkpoints.db"):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints';")
        if not cursor.fetchone():
            conn.close()
            return []
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"⚠️ 数据库读取错误: {e}")
        return []


# ==========================================
# 2. 核心智能体初始化工厂函数
# ==========================================
def build_agent(memory):
    # 1. 初始化大模型
    # 确保本地 Ollama 已经启动了 qwen2.5:7b 模型
    llm = ChatOllama(model="qwen2.5:7b", temperature=0.2, base_url="http://127.0.0.1:11434")


    tools = []

    # 返回组装好的智能体
    return create_react_agent(llm, tools, checkpointer=memory)

