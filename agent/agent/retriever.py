import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL,
    DOCS_DIR, VECTORSTORE_DIR, TOP_K,
)

class KnowledgeRetriever:
    """知识库检索器：负责文档切分、向量化、相似度检索"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
        )
        self.vectorstore = None
        self._load_or_build()

    def _load_or_build(self):
        if os.path.exists(VECTORSTORE_DIR) and os.listdir(VECTORSTORE_DIR):
            self.vectorstore = Chroma(
                persist_directory=VECTORSTORE_DIR,
                embedding_function=self.embeddings,
            )
            print("✓ 已加载向量数据库")
        else:
            print("⚠ 向量数据库不存在，正在构建 ...")
            self.build_vectorstore()

    def build_vectorstore(self):
        documents = self._load_documents()
        if not documents:
            print("⚠ 未在 knowledge_base/docs 找到任何文档")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "],
        )
        chunks = splitter.split_documents(documents)
        print(f"✓ 共切分 {len(chunks)} 个文档片段")

        os.makedirs(VECTORSTORE_DIR, exist_ok=True)
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=VECTORSTORE_DIR,
        )
        self.vectorstore.persist()
        print("✓ 向量数据库构建完成")

    def _load_documents(self):
        documents = []
        if not os.path.exists(DOCS_DIR):
            os.makedirs(DOCS_DIR, exist_ok=True)
            return documents

        for filename in os.listdir(DOCS_DIR):
            filepath = os.path.join(DOCS_DIR, filename)
            try:
                if filename.lower().endswith(".txt") or filename.lower().endswith(".md"):
                    loader = TextLoader(filepath, encoding="utf-8")
                elif filename.lower().endswith(".pdf"):
                    loader = PyPDFLoader(filepath)
                else:
                    continue

                docs = loader.load()
                for d in docs:
                    d.metadata["source"] = filename
                documents.extend(docs)
                print(f"  加载: {filename}")
            except Exception as e:
                print(f"  ✗ 加载失败 {filename}: {e}")
        return documents

    def search(self, query: str, k: int = TOP_K):
        if not self.vectorstore:
            return []
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": float(score),
            }
            for doc, score in results
        ]
