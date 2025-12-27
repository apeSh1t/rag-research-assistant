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
        
        # 显示调试信息
        print(f"🔍 Query: '{query}' - Search results:")
        for i, res in enumerate(results):
            title = res['metadata'].get('source', 'Unknown')
            print(f"  {i+1}. Score: {res['score']:.4f} - {title}")
        
        # 格式化输出
        formatted_results = []
        for res in results:
            # EnhancedVectorStore 返回的是 distance，越小越好。
            # 但这里我们假设它返回的是 distance。
            # 如果是 cosine distance, 0 是完全相同。
            # 之前的代码过滤 score >= 1.0 (distance)。
            if res['score'] >= 1.0: 
                continue
                
            title = res['metadata'].get('source', '未命名')
            content = res['text'] # 原始文本
            context = res['metadata'].get('context_str', '')
            
            # 展示时带上上下文信息
            display_text = f"【{title}】\n"
            if context:
                display_text += f"Context: {context}\n"
            display_text += f"{content}"
            
            formatted_results.append(display_text)

        formatted = "\n\n".join(formatted_results)
        
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
            
            sources = set([meta.get('source', 'Unknown') for meta in all_docs['metadatas']])
            return f"知识库包含 {len(sources)} 个文档:\n" + "\n".join(f"- {s}" for s in sources)
        except Exception as e:
            return f"获取文档列表失败: {e}"
    
    def add_document(self, file_path: str, title: str = None):
        """
        通用文档添加方法，支持 PDF (使用 Enhanced System)
        """
        if self.vector_store is None:
            return {"success": False, "message": "Knowledge base not loaded"}
        
        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()
        doc_title = title or file_path_obj.name
        
        print(f"  [KB] 正在处理文档: {doc_title} ({file_ext})")
        
        try:
            if file_ext == '.pdf':
                print(f"  [KB] 使用 Enhanced PDF Processor 处理...")
                # 1. PDF -> JSON Structure
                json_doc = PDFProcessor.process(str(file_path))
                print(f"  [KB] PDF 处理完成，开始分块...")
                # 2. Chunking with Hierarchy
                chunker = DotsHierarchicalChunker(chunk_size=500, chunk_overlap=50)
                chunks = chunker.chunk(json_doc)
                print(f"  [KB] 分块完成，开始写入向量库...")
                # 3. Store
                self.vector_store.add_chunks(chunks, source_file=doc_title)
                print(f"  [KB] 向量库写入成功!")
                return {
                    "success": True,
                    "message": f"成功索引 {len(chunks)} 个片段",
                    "chunks": len(chunks),
                    "title": doc_title
                }
            elif file_ext == '.md':
                print(f"  [KB] 使用 Enhanced Markdown Processor 处理...")
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
                    "message": f"成功索引 {len(chunks)} 个片段",
                    "chunks": len(chunks),
                    "title": doc_title
                }
            else:
                return {"success": False, "message": "目前 Enhanced System 仅支持 PDF 和 MD 文件"}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"索引失败: {str(e)}"}

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