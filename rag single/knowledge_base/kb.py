from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
    
    def add_document(self, file_path: str, title: str = None):
        """
        通用文档添加方法，支持 PDF, DOCX, TXT, MD
        """
        if self.vector_store is None:
            return {"success": False, "message": "Knowledge base not loaded"}
        
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()
        doc_title = title or file_path_obj.name
        
        print(f"  [KB] 正在处理文档: {doc_title} ({file_ext})")
        
        try:
            documents = []
            if file_ext == '.pdf':
                print(f"  [KB] 正在加载 PDF 内容...")
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(str(file_path))
                    documents = loader.load()
                except Exception:
                    import PyPDF2
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                from langchain_core.documents import Document
                                documents.append(Document(page_content=text))
            
            elif file_ext == '.docx':
                print(f"  [KB] 正在加载 Word 内容...")
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(file_path))
                documents = loader.load()
                
            elif file_ext in ['.txt', '.md']:
                print(f"  [KB] 正在加载文本内容...")
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(str(file_path), encoding='utf-8')
                documents = loader.load()
            
            if not documents:
                return {"success": False, "message": f"未能从文件 {file_ext} 中提取内容"}

            print(f"  [KB] 内容提取完成, 正在进行文本切分...")
            # 添加元数据
            for doc in documents:
                doc.metadata['title'] = doc_title
                doc.metadata['source'] = str(file_path_obj.name)
            
            # 分割文本
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", " "]
            )
            split_docs = text_splitter.split_documents(documents)
            
            print(f"  [KB] 切分完成, 共有 {len(split_docs)} 个片段。正在调用 Embedding 模型写入向量库...")
            print(f"  [KB] 注意: 如果是首次运行, 模型加载可能需要 1-2 分钟...")
            
            # 添加到向量库
            self.vector_store.add_documents(split_docs)
            
            print(f"  [KB] 向量库写入成功!")
            return {
                "success": True,
                "message": f"成功索引 {len(split_docs)} 个片段",
                "chunks": len(split_docs),
                "title": doc_title
            }
            
        except Exception as e:
            return {"success": False, "message": f"索引失败: {str(e)}"}

    def add_pdf_document(self, pdf_path: str, title: str = None):
        """保持向后兼容"""
        return self.add_document(pdf_path, title)

    def delete_document(self, title: str):
        """从向量库中删除文档"""
        if self.vector_store is None:
            return False
        try:
            # 1. 查找具有该 title 的所有文档的 ID
            # Chroma 的 get 方法支持 where 过滤
            results = self.vector_store.get(where={"title": title})
            ids = results.get("ids", [])
            
            if ids:
                # 2. 按 ID 删除
                self.vector_store.delete(ids=ids)
                return True
            return False
        except Exception as e:
            print(f"Error deleting document from vector store: {e}")
            return False