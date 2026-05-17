
# 运行步骤

1. 创建虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置 API Key
   ```bash
   cp .env.example .env
   cp .env.example .env OPENAI_API_KEY
   ```

4. 启动应用
   ```bash
   streamlit run app.py
   ```

打开浏览器访问 http://localhost:8501 即可使用。

---

# 系统架构图 (Agent 决策流)

- **用户提问**
  - KnowledgeRetriever
    - 向量检索 Top-K 文档片段
  - LLM 生成回答
    - 智能体反馈 + 工单解决判断
  - 置信度 = 是 → 直接返回员工
  - 置信度 = 否 → 返回答案

- **TicketSystem**
  - 自动生成工单 + 分派部门 + 通知负责人

- **返回结果 + 工单号**
