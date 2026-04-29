import streamlit as st
import requests
import time
import uuid

# ==========================================
# 1. 页面配置与全局变量
# ==========================================
st.set_page_config(page_title="AI 深度研究员 (微服务版)", page_icon="🌐", layout="wide")
st.title("🌐 AI 深度研究员 (全栈微服务架构)")

# 🌟 FastAPI 后端的真实地址
API_URL = "http://127.0.0.1:8000/api/v1/chat"

# ==========================================
# 2. 侧边栏：只负责传递身份标识，不再读取数据库
# ==========================================
with st.sidebar:
    st.header("⚙️ 客户端设置")
    st.markdown("当前处于 **完全解耦模式**。")

    # 提取公共 Headers (包含鉴权和 Ngrok 穿透)
    # ⚠️ 记得换成你自己的真实 API Key 和 Ngrok 地址的 Base 部分
    API_BASE = "http://127.0.0.1:8000/api/v1"
    HEADERS = {
        "ngrok-skip-browser-warning": "true",
        "X-API-Key": "sk-my-super-secret-key-2026"
    }


    # --- 新增功能：从后端拉取历史 Thread ID ---
    @st.cache_data(ttl=5)  # 缓存 5 秒，防止频繁请求
    def fetch_history_threads():
        try:
            res = requests.get(f"{API_BASE}/threads", headers=HEADERS, timeout=5)
            if res.status_code == 200:
                return res.json().get("threads", [])
        except:
            return []
        return []

    history_threads = fetch_history_threads()

    # 组装下拉菜单选项：第一项永远是新建会话
    options = ["➕ 新建会话 (New Session)"] + history_threads

    selected_option = st.selectbox("📂 选择或新建会话:", options)

    if selected_option == "➕ 新建会话 (New Session)":
        # 如果是新建，生成一个随机 UUID 让用户确认或修改
        if "new_session_id" not in st.session_state:
            st.session_state.new_session_id = f"web_{str(uuid.uuid4())[:4]}"
        current_thread_id = st.text_input("给新会话起个名字:", value=st.session_state.new_session_id)
    else:
        # 如果选了历史记录，就直接使用选中的 ID
        current_thread_id = selected_option
        st.success(f"已加载历史记忆核心: {current_thread_id}")

    st.markdown("---")



    def fetch_thread_history(thread_id):
        """向后端请求特定会话的历史聊天记录"""
        try:
            # 去请求我们刚才在后端新写的那个 /history 接口
            res = requests.get(f"{API_BASE}/history/{thread_id}", headers=HEADERS, timeout=5)
            if res.status_code == 200:
                return res.json().get("messages", [])
        except Exception as e:
            st.warning(f"无法拉取历史记忆: {e}")
        return []


    # 🌟 当用户在左侧切换下拉菜单时，触发记忆同步
    if "last_thread" not in st.session_state or st.session_state.last_thread != current_thread_id:
        # 记录当前正在看的 thread_id，防止无限循环拉取
        st.session_state.last_thread = current_thread_id
        # 判断逻辑：如果是刚新建的会话，不需要去后端拉，直接给个欢迎语
        if current_thread_id == st.session_state.get("new_session_id"):
            st.session_state.messages = [
                {"role": "assistant", "content": "你好！这是一个全新的多模态会话。请问要查阅哪篇文档？"}]
        else:
            # 如果选的是历史会话，显示加载动画，并去后端要数据
            with st.spinner("⏳ 正在从云端大脑同步历史记忆..."):
                history = fetch_thread_history(current_thread_id)
                if history:
                    st.session_state.messages = history
                else:
                    st.session_state.messages = [{"role": "assistant", "content": "记忆核心已连接。请问有什么可以效劳？"}]

# ==========================================
# 3. 前端状态管理 (纯 UI 层面的展示缓存)
# ==========================================
if "messages" not in st.session_state or st.session_state.get("last_thread") != current_thread_id:
    st.session_state.messages = [{"role": "assistant",
                                  "content": "你好！我是部署在后端的 AI 引擎，已通过 RESTful API 与前端建立连接。请问有什么可以效劳？"}]
    st.session_state.last_thread = current_thread_id

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. 核心网络通信：向后端 API 发送请求
# ==========================================
if user_input := st.chat_input("请输入指令..."):
    # 显示用户的提问
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        with st.spinner("📡 正在通过 HTTP POST 发送数据包到后端..."):
            try:
                # 🌟 核心：构造 JSON 载荷
                payload = {
                    "thread_id": current_thread_id,
                    "message": user_input
                }

                # 发起网络请求 (类似你在网页上点击按钮的底层动作)
                headers = {
                    "ngrok-skip-browser-warning": "true",
                    "X-API-Key": "sk-my-super-secret-key-2026"
                }
                response = requests.post(API_URL, json=payload,headers=headers, timeout=120)

                # 如果后端返回 200 (成功)
                if response.status_code == 200:
                    result_data = response.json()
                    # 提取后端返回的真正答案
                    final_answer = result_data.get("reply", "后端未返回有效内容")

                    # 💡 UX 优化：因为目前的 API 是一次性返回全部结果，
                    # 为了保持打字机体验，我们在前端写一个小循环，做个“伪流式”特效
                    displayed_text = ""
                    for char in final_answer:
                        displayed_text += char
                        message_placeholder.markdown(displayed_text + "▌")
                        time.sleep(0.015)  # 假装在打字

                    # 定格最终画面
                    message_placeholder.markdown(final_answer)
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})

                else:
                    st.error(f"后端报错: HTTP {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 无法连接到后端服务器！请检查终端 1 中的 api_server.py 是否已经启动运行。")
            except Exception as e:
                st.error(f"发生网络未知错误: {e}")