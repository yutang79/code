import json
import re
from langchain_openai import ChatOpenAI
from agent.retriever import KnowledgeRetriever
from agent.ticket import TicketSystem
from agent.prompts import QA_SYSTEM_PROMPT, QA_USER_PROMPT, CLASSIFY_PROMPT
from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL,
    CONFIDENCE_THRESHOLD,
)

class QAAgent:
    """
    Agent 主流程：
      问题 → 检索知识库 → LLM 生成回答 → 自评置信度
           → 高置信度直接回 / 低置信度自动开工单
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
            temperature=0.2,
        )
        self.retriever = KnowledgeRetriever()
        self.ticket_system = TicketSystem()

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "answer": text,
            "confidence": "low",
            "reason": "JSON 解析失败",
            "need_ticket": True,
            "department": "Other",
            "summary": "",
        }

    def classify_department(self, question: str) -> str:
        resp = self.llm.invoke(CLASSIFY_PROMPT.format(question=question))
        dept = resp.content.strip().split()[0] if resp.content else "Other"
        return dept if dept in {"IT", "HR", "Finance", "Admin", "Other"} else "Other"

    def answer(self, question: str, user: str = "anonymous") -> dict:
        # === Step 1. RAG 检索 ===
        retrieved = self.retriever.search(question)
        context = (
            "\n\n---\n\n".join(
                f"【来源：{r['source']}】\n{r['content']}" for r in retrieved
            )
            if retrieved else "（暂无相关文档）"
        )

        # === Step 2. LLM 生成回答 ===
        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": QA_USER_PROMPT.format(
                context=context, question=question)},
        ]
        resp = self.llm.invoke(messages)
        result = self._parse_json(resp.content)

        # === Step 3. 置信度判断 + 自动开工单 ===
        conf_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
        score = conf_map.get(result.get("confidence", "low"), 0.3)

        ticket_info = None
        if result.get("need_ticket") or score < CONFIDENCE_THRESHOLD:
            department = result.get("department") or self.classify_department(question)
            summary = result.get("summary") or question[:80]

            ticket_info = self.ticket_system.create_ticket(
                user=user,
                question=question,
                summary=summary,
                department=department,
                context=context,
            )

        return {
            "question": question,
            "answer": result.get("answer", ""),
            "confidence": result.get("confidence", "low"),
            "reason": result.get("reason", ""),
            "sources": list({r["source"] for r in retrieved}),
            "retrieved": retrieved,
            "ticket": ticket_info,
        }
