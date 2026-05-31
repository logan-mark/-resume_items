import streamlit as st
import requests
import uuid
import json
import codecs
st.set_page_config(page_title="AI 深度研究员", page_icon="🌐", layout="wide")
st.title("🌐 AI 深度研究员 (全栈微服务架构)")

API_BASE = "http://127.0.0.1:8000/api/v1"
HEADERS = {"X-API-Key": "sk-my-super-secret-key-2026"}

with st.sidebar:
    st.header("⚙️ 会话管理")


    @st.cache_data(ttl=2)
    def fetch_history_threads():
        try:
            res = requests.get(f"{API_BASE}/threads", headers=HEADERS, timeout=5)
            if res.status_code == 200:
                return res.json().get("threads", [])
        except:
            return []
        return []


    history_threads = fetch_history_threads()
    options = ["➕ 新建会话 (New Session)"] + history_threads
    selected_option = st.selectbox("📂 选择或新建会话:", options)

    if selected_option == "➕ 新建会话 (New Session)":
        if "new_session_id" not in st.session_state:
            st.session_state.new_session_id = f"web_{str(uuid.uuid4())[:4]}"
        current_thread_id = st.text_input("给新会话起个名字:", value=st.session_state.new_session_id)
    else:
        current_thread_id = selected_option
        st.success(f"已加载会话: {current_thread_id}")


    def fetch_thread_history(thread_id):
        try:
            res = requests.get(f"{API_BASE}/history/{thread_id}", headers=HEADERS, timeout=5)
            if res.status_code == 200:
                return res.json().get("messages", [])
        except Exception as e:
            st.warning("⚠️ 无法拉取历史记录，后端可能未启动。")
        return []


    if st.session_state.get("last_thread") != current_thread_id:
        st.session_state.last_thread = current_thread_id
        if current_thread_id == st.session_state.get("new_session_id"):
            st.session_state.messages = [
                {"role": "assistant", "content": "你好！我是你的 AI 深度研究员，请问有什么可以效劳？"}]
        else:
            with st.spinner("⏳ 正在同步历史记忆..."):
                history = fetch_thread_history(current_thread_id)
                st.session_state.messages = history if history else [{"role": "assistant", "content": "记忆已连接。"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("请输入指令..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            payload = {"thread_id": current_thread_id, "message": user_input}
            # stream=True 是灵魂
            response = requests.post(f"{API_BASE}/chat", json=payload, headers=HEADERS, stream=True, timeout=120)

            if response.status_code == 200:
                def stream_generator():
                    # 💡 增量解码器：它就像个完美的拼图板，哪怕网络把一个汉字劈成了两半，
                    # 它也会先把前半部分存起来，等下一批数据到了拼成完整汉字再吐出来，绝不报错卡死！
                    decoder = codecs.getincrementaldecoder('utf-8')()

                    # 💡 chunk_size=None：意思是绝不缓冲！网卡收到哪怕 1 个字节，也立刻给我！
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            text = decoder.decode(chunk)
                            if text:
                                yield text

                    # 收尾操作
                    final_text = decoder.decode(b'', final=True)
                    if final_text:
                        yield final_text


                # 完美对接 Streamlit 官方的最强打字机渲染器
                full_response = st.write_stream(stream_generator)

                if full_response:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.warning("⚠️ 没有收到回答，请重新提问。")

            else:
                st.error(f"后端报错: HTTP {response.status_code} - {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("🚨 无法连接到后端服务器！请检查 api_server.py 是否已启动。")
        except Exception as e:
            st.error(f"发生网络错误: {e}")