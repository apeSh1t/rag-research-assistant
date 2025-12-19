#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build English knowledge base index
"""

import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

def build_english_index():
    """构建英文知识库索引"""
    print("🔨 Building English knowledge base index...")
    
    # 设置路径
    kb_dir = Path("knowledge_base/problems_en")
    persist_dir = Path("chroma_db_en")
    
    if not kb_dir.exists():
        print(f"❌ English knowledge base directory does not exist: {kb_dir}")
        return
    
    # 删除旧的向量库（如果可能的话）
    if persist_dir.exists():
        import shutil
        try:
            shutil.rmtree(persist_dir)
            print("🗑️ Removed old vector store")
        except OSError:
            print("⚠️ Could not remove old vector store, will overwrite")
    
    try:
        # 加载英文文档
        loader = DirectoryLoader(
            str(kb_dir),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        documents = loader.load()
        print(f"📚 Loaded {len(documents)} English documents")
        
        # 显示文档内容
        for i, doc in enumerate(documents):
            print(f"\nDocument {i+1}: {doc.metadata.get('source', 'Unknown')}")
            print(f"Content length: {len(doc.page_content)}")
            print(f"First 100 chars: {doc.page_content[:100]}...")
        
        # 文本分割 - 增加切片大小以保留更多上下文
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # 增加到1500字符，保留更多完整信息
            chunk_overlap=50,  # 增加重叠以保持上下文连贯性
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " "]
        )
        split_docs = text_splitter.split_documents(documents)
        print(f"📄 Split into {len(split_docs)} document chunks")
        
        # 使用更优秀的英文嵌入模型
        embeddings = SentenceTransformerEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"  # 目前最好的英文检索模型之一
            # 其他选择:
            # "sentence-transformers/all-mpnet-base-v2"  # 经典高质量模型
            # "sentence-transformers/all-MiniLM-L12-v2"  # 平衡准确性和速度
        )
        
        # 创建向量库
        vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            collection_name="mixing_kb_en",
            persist_directory=str(persist_dir)
        )
        
        print("✅ English knowledge base index built successfully!")
        
        # 测试检索
        print("\n🔍 Testing retrieval:")
        test_queries = ["RGB color conversion", "multi-component mixing", "dye preparation"]
        
        for query in test_queries:
            results = vector_store.similarity_search_with_score(query, k=3)
            print(f"\nQuery: '{query}'")
            for i, (result, score) in enumerate(results):
                print(f"  Result {i+1} (score: {score:.4f}): {result.page_content[:50]}...")
                print(f"  Source: {result.metadata.get('source', 'Unknown')}")
        
        return vector_store
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    build_english_index()