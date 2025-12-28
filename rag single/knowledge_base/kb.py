from pathlib import Path
import tempfile
from knowledge_base.enhanced_system import EnhancedVectorStore, DotsHierarchicalChunker, PDFProcessor

class KnowledgeBase:
    def __init__(self, kb_dir: str = "knowledge_base", use_english: bool = True):
        self.kb_dir = Path(kb_dir)
        self.use_english = use_english
        self.vector_store = None
        self._load_vector_store()
    
    def _load_vector_store(self):
        # 根据语言选择不同的向量库目录
        if self.use_english:
            persist_dir = Path(tempfile.gettempdir()) / "faiss_db_en"
            collection_name = "mixing_kb_en"
        else:
            persist_dir = Path(tempfile.gettempdir()) / "faiss_db"
            collection_name = "mixing_kb"
        
        # 使用 EnhancedVectorStore
        self.vector_store = EnhancedVectorStore(
            persist_directory=str(persist_dir),
            collection_name=collection_name
        )
    
    def retrieve(self, query: str, k: int = 3) -> str:
        """检索知识库"""
        if self.vector_store is None:
            return "知识库未加载" if not self.use_english else "Knowledge base not loaded"
        
        results = self.vector_store.retrieve(query, top_k=k)
        
        if not results:
            return f"未找到与'{query}'相关的信息" if not self.use_english else f"No information found for '{query}'"
        
        # 显示调试信息（相似度越高越好）
        print(f"🔍 Query: '{query}' - Search results:")
        for i, res in enumerate(results):
            title = res['metadata'].get('source', 'Unknown')
            print(f"  {i+1}. Score: {res['score']:.4f} - {title}")
        
        # 格式化输出
        # 先按相似度降序
        sorted_results = sorted(results, key=lambda r: r.get('score', 0), reverse=True)

        formatted_results = []
        for res in sorted_results:
            title = res['metadata'].get('source', 'Untitled')
            content = res['text']  # 原始文本
            context = res['metadata'].get('context_str', '')
            
            # 展示时带上上下文信息
            display_text = f"[{title}]\n"
            if context:
                display_text += f"Context: {context}\n"
            display_text += f"{content}"
            
            formatted_results.append(display_text)

        formatted = "\n\n".join(formatted_results)
        
        if not formatted:
             return f"未找到与'{query}'高度相关的信息" if not self.use_english else f"No highly relevant information found for '{query}'"
        
        return formatted

    def retrieve_structured(self, query: str, k: int = 5):
        """返回结构化的 chunk_info 列表，包含层级/标题等信息。"""
        if self.vector_store is None:
            return []
        return self.vector_store.retrieve_structured(query, top_k=k)
    
    def list_documents(self):
        """列出所有文档"""
        if self.vector_store is None:
            return "Knowledge base not loaded"
        
        try:
            # 获取所有文档信息
            all_docs = self.vector_store.get()
            if not all_docs['metadatas']:
                return "No documents in knowledge base"
            
            sources = set([meta.get('source', 'Unknown') for meta in all_docs['metadatas']])
            return f"Knowledge base contains {len(sources)} documents:\n" + "\n".join(f"- {s}" for s in sources)
        except Exception as e:
            return f"Failed to list documents: {e}"
    
    def add_document(self, file_path: str, title: str = None):
        """
        通用文档添加方法，支持 PDF (使用 Enhanced System)
        """
        if self.vector_store is None:
            return {"success": False, "message": "Knowledge base not loaded"}
        
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()
        doc_title = title or file_path_obj.name
        
        print(f"  [KB] Processing document: {doc_title} ({file_ext})")
        
        try:
            if file_ext == '.pdf':
                print(f"  [KB] Using Enhanced PDF Processor...")
                # 1. PDF -> JSON Structure
                json_doc = PDFProcessor.process(str(file_path))
                print(f"  [KB] PDF processing complete, starting chunking...")
                # 2. Chunking with Hierarchy
                chunker = DotsHierarchicalChunker(chunk_size=500, chunk_overlap=50)
                chunks = chunker.chunk(json_doc)
                print(f"  [KB] Chunking complete, starting write to vector store...")
                # 3. Store
                self.vector_store.add_chunks(chunks, source_file=doc_title)
                print(f"  [KB] Write to vector store successful!")
                return {
                    "success": True,
                    "message": f"Successfully indexed {len(chunks)} chunks",
                    "chunks": len(chunks),
                    "title": doc_title
                }
            elif file_ext == '.md':
                print(f"  [KB] Using Enhanced Markdown Processor...")
                # 模拟 PDFProcessor 的输出结构
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                layout_info = []
                for line in content.split('\n'):
                    line = line.strip()
                    if not line: continue
                    layout_info.append({
                        "text": line,
                        "category": "Section-header" if line.startswith('#') else "Text",
                        "page_no": 1
                    })
                
                json_doc = [{"page_no": 1, "full_layout_info": layout_info}]
                chunker = DotsHierarchicalChunker(chunk_size=500, chunk_overlap=50)
                chunks = chunker.chunk(json_doc)
                self.vector_store.add_chunks(chunks, source_file=doc_title)
                
                return {
                    "success": True,
                    "message": f"Successfully indexed {len(chunks)} chunks",
                    "chunks": len(chunks),
                    "title": doc_title
                }
            else:
                return {"success": False, "message": "Currently Enhanced System only supports PDF and MD files"}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Indexing failed: {str(e)}"}

    def add_pdf_document(self, pdf_path: str, title: str = None):
        """保持向后兼容"""
        return self.add_document(pdf_path, title)

    def delete_document(self, title: str):
        """从向量库中删除文档"""
        if self.vector_store is None:
            return False
        try:
            # 查找属于该 title/source 的所有条目并删除
            results = self.vector_store.get(where={"source": title})
            ids = results.get("ids", []) if results else []
            if ids:
                self.vector_store.delete(ids=ids)
            else:
                # fallback delete by where to ensure cleanup
                self.vector_store.delete(where={"source": title})
            return True
        except Exception as e:
            print(f"Error deleting document from vector store: {e}")
            return False