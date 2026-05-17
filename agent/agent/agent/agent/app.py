import os
import streamlit as st
from agent.core import QAAgent
from config import DOCS_DIR

st.set_page_config(page_title="企业知识库 AI 助手", page_icon="🤖", layout="wide")

@st.cache_resource(show_spinner="正在初始化 Agent ...")
def get_agent():
    return QAAgent()

st.title("🤖 企业知识库 AI 助手")
st.caption("基于大模型的智能问答与工单自助系统")

with st.sidebar:
    st.header("⚙️ 设置")
    user = st.text_input("您的工号 / 姓名", value="employee001")
    st.divider()
    page = st.radio("功能", ["💬 智能问答", "📋 工单管理", "🛠️ 知识库管理"])

agent = get_agent()

# ============== 智能问答 ==============
if page == "💬 智能问答":
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "extra" in msg:
                with st.expander("🔍 检索详情"):
                    st.json(msg["extra"])

    if question := st.chat_input("请输入您的问题，例如：报销流程是什么？"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Agent 思考中 ..."):
                result = agent.answer(question, user=user)

            content = f"**📝 回答**\n\n{result['answer']}\n\n"
            content += f"**📊 置信度**：`{result['confidence']}` — {result['reason']}\n\n"
            if result["sources"]:
                content += f"**📚 来源**：{', '.join(result['sources'])}\n\n"
            if result["ticket"]:
                t = result["ticket"]
                content += (
                    "---\n"
                    "📨 **检测到无法自动解答，已为您创建工单：**\n\n"
                    f"- 工单号：`{t['ticket_no']}`\n"
                    f"- 转交部门：**{t['department']}**\n"
                    f"- 负责人：{t['owner']}\n"
                    f"- 状态：{t['status']}\n"
                )
            st.markdown(content)
            st.session_state.messages.append(
                {"role": "assistant", "content": content, "extra": result}
            )

# ============== 工单管理 ==============
elif page == "📋 工单管理":
    st.header("📋 工单列表")
    status = st.selectbox("筛选状态", ["全部", "open", "in_progress", "closed"])
    tickets = agent.ticket_system.list_tickets(
        status=None if status == "全部" else status
    )

    if not tickets:
        st.info("暂无工单")
    for t in tickets:
        with st.expander(f"🎫 {t['ticket_no']}  |  {t['department']}  |  状态：{t['status']}"):
            st.write(f"**提交人：** {t['user']}")
            st.write(f"**原始问题：** {t['question']}")
            st.write(f"**问题摘要：** {t['summary']}")
            st.write(f"**负责人：** {t['owner']}")
            st.write(f"**创建时间：** {t['created_at']}")

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("▶️ 处理中", key=f"p_{t['ticket_no']}"):
                    agent.ticket_system.update_status(t["ticket_no"], "in_progress")
                    st.rerun()
            with c2:
                if st.button("✅ 关闭", key=f"c_{t['ticket_no']}"):
                    agent.ticket_system.update_status(t["ticket_no"], "closed")
                    st.rerun()
            with c3:
                if st.button("🔄 重新打开", key=f"r_{t['ticket_no']}"):
                    agent.ticket_system.update_status(t["ticket_no"], "open")
                    st.rerun()

# ============== 知识库管理 ==============
else:
    st.header("🛠️ 知识库管理")
    st.write(f"将文档（.txt / .md / .pdf）放入：`{DOCS_DIR}`")
    if st.button("🔄 重建向量索引"):
        with st.spinner("正在重建 ..."):
            agent.retriever.build_vectorstore()
        st.success("✓ 重建完成，请重启应用")

    if os.path.exists(DOCS_DIR):
        files = os.listdir(DOCS_DIR)
        st.write(f"📁 已加载文档（{len(files)} 个）")
        for f in files:
            st.write(f"- {f}")
