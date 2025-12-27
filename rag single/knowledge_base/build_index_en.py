#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build English knowledge base index
"""

import os
import sys
from pathlib import Path

# 将 rag single 目录添加到 Python 路径，以便能够导入 knowledge_base 模块
current_file_path = Path(__file__).parent.absolute()
sys.path.append(str(current_file_path.parent))

from knowledge_base.kb import KnowledgeBase

def build_english_index():
    """构建英文知识库索引"""
    print("🔨 Building English knowledge base index...")
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()
    # 根目录 (rag single)
    root_dir = current_dir.parent
    
    # 设置路径
    kb_dir = current_dir / "problems_en"
    
    if not kb_dir.exists():
        print(f"❌ English knowledge base directory does not exist: {kb_dir}")
        return
    
    try:
        # 初始化 KnowledgeBase (它会自动处理向量库的创建和加载)
        # 注意：KnowledgeBase 内部现在使用的是 EnhancedVectorStore
        kb = KnowledgeBase(kb_dir=str(current_dir), use_english=True)
        
        # 获取所有 md 文件
        md_files = list(kb_dir.glob("*.md"))
        print(f"📚 Found {len(md_files)} English documents")
        
        for file_path in md_files:
            print(f"📄 Processing: {file_path.name}")
            # 使用新的 add_document 方法 (内部会调用 EnhancedMarkdownChunker)
            # 注意：虽然 add_document 目前主要针对 PDF，但我们可以稍微调整一下 kb.py 
            # 或者在这里直接模拟处理。
            # 为了保持一致性，我们直接调用 kb.add_document
            result = kb.add_document(str(file_path))
            if result.get("success"):
                print(f"  ✅ Indexed {result.get('chunks')} chunks")
            else:
                print(f"  ❌ Failed: {result.get('message')}")
        
        print("\n✅ English knowledge base index built successfully!")
        
        # 测试检索
        print("\n🔍 Testing retrieval:")
        test_queries = ["RGB color conversion", "multi-component mixing", "dye preparation"]
        
        for query in test_queries:
            results = kb.retrieve(query, k=2)
            print(f"\nQuery: '{query}'")
            print(results)
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    build_english_index()