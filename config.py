import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL       = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR        = os.path.join(BASE_DIR, "knowledge_base", "docs")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "knowledge_base", "vectorstore")
TICKETS_DB      = os.path.join(BASE_DIR, "data", "tickets.db")

CONFIDENCE_THRESHOLD = 0.7
TOP_K = 4

# 部门负责人映射（生产环境可对接 LDAP/飞书/钉钉）
DEPARTMENT_OWNERS = {
    "IT":      "it-support@company.com",
    "HR":      "hr@company.com",
    "Finance": "finance@company.com",
    "Admin":   "admin@company.com",
    "Other":   "support@company.com",
}
