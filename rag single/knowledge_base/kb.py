from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

class KnowledgeBase:
    def __init__(self, kb_dir: str = "knowledge_base", use_english: bool = True):
        self.kb_dir = Path(kb_dir)
        self.use_english = use_english
        self.embedding_model = SentenceTransformerEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"  # 使用更优秀的英文检索模型
        )
        self.vector_store = None
        self._load_vector_store()
    
    def _load_vector_store(self):
        # 根据语言选择不同的向量库目录
        if self.use_english:
            persist_dir = self.kb_dir.parent / "chroma_db_en"
            collection_name = "mixing_kb_en"
        else:
            persist_dir = self.kb_dir.parent / "chroma_db"
            collection_name = "mixing_kb"
        
        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Vector store does not exist: {persist_dir}\n"
                "Please run: python knowledge_base/build_index.py first"
            )
        
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(persist_dir)
        )
    
    def retrieve(self, query: str, k: int = 3) -> str:
        """检索知识库"""
        if self.vector_store is None:
            return "知识库未加载" if not self.use_english else "Knowledge base not loaded"
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        if not results:
            return f"未找到与'{query}'相关的信息" if not self.use_english else f"No information found for '{query}'"
        
        # 显示调试信息
        print(f"🔍 Query: '{query}' - Search results:")
        for i, (doc, score) in enumerate(results):
            title = doc.metadata.get('title', 'Unknown')
            print(f"  {i+1}. Score: {score:.4f} - {title}")
        
        # 添加相似度过滤，只返回高质量匹配
        formatted = "\n\n".join([
            f"【{doc.metadata.get('title', '未命名')}】(Score: {score:.4f})\n{doc.page_content}"
            for doc, score in results if score < 1.0  # 调整阈值以过滤低质量匹配
        ])
        
        return formatted if formatted else f"未找到与'{query}'高度相关的信息"
    
    def list_documents(self):
        """列出所有文档"""
        if self.vector_store is None:
            return "知识库未加载"
        
        try:
            # 获取所有文档信息
            all_docs = self.vector_store.get()
            if not all_docs['metadatas']:
                return "知识库中没有文档"
            
            titles = [meta.get('title', 'Unknown') for meta in all_docs['metadatas']]
            return f"知识库包含 {len(titles)} 个文档:\n" + "\n".join(f"- {title}" for title in titles)
        except Exception as e:
            return f"获取文档列表失败: {e}"