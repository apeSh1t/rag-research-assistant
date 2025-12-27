from typing import List, Dict, Any
from langchain_core.documents import Document

class EnhancedMarkdownChunker:
    """
    移植自 DotsHierarchicalChunker 的逻辑，专门用于处理 Markdown 文件。
    核心功能：在切分文本时保留层级上下文（标题路径）。
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _get_heading_level(self, line: str) -> int:
        """判断 Markdown 标题层级"""
        line = line.strip()
        if not line.startswith('#'):
            return 0
        
        level = 0
        for char in line:
            if char == '#':
                level += 1
            else:
                break
        return level

    def split_text(self, text: str) -> List[Document]:
        """
        切分 Markdown 文本，返回带有 context metadata 的 Document 对象列表
        """
        lines = text.split('\n')
        
        chunks = []
        current_chunk_lines = []
        current_length = 0
        
        # 维护标题栈，例如 ["一级标题", "二级标题"]
        heading_stack = []
        
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
                
            level = self._get_heading_level(stripped_line)
            
            # 如果遇到新标题
            if level > 0:
                # 1. 如果当前缓冲区有内容，先保存为一个 chunk
                if current_chunk_lines:
                    self._add_chunk(chunks, current_chunk_lines, heading_stack)
                    current_chunk_lines = []
                    current_length = 0
                
                # 2. 更新标题栈
                # 清除当前层级及更深层级的旧标题
                heading_text = stripped_line.lstrip('#').strip()
                heading_stack = heading_stack[:level-1]
                heading_stack.append(heading_text)
                
                # 标题本身也作为上下文的一部分，不一定要单独成块，
                # 但为了连贯性，我们可以选择将标题行加入下一个块，或者仅作为 metadata
                continue

            # 普通文本行处理
            # 检查是否超长
            if current_length + len(stripped_line) > self.chunk_size and current_chunk_lines:
                self._add_chunk(chunks, current_chunk_lines, heading_stack)
                # 处理重叠 (Overlap)
                # 简单的重叠策略：保留最后几行
                overlap_len = 0
                new_lines = []
                for prev_line in reversed(current_chunk_lines):
                    if overlap_len + len(prev_line) < self.chunk_overlap:
                        new_lines.insert(0, prev_line)
                        overlap_len += len(prev_line)
                    else:
                        break
                current_chunk_lines = new_lines
                current_length = overlap_len

            current_chunk_lines.append(stripped_line)
            current_length += len(stripped_line)
            
        # 处理最后一个块
        if current_chunk_lines:
            self._add_chunk(chunks, current_chunk_lines, heading_stack)
            
        return chunks

    def _add_chunk(self, chunks: List[Document], lines: List[str], heading_stack: List[str]):
        """构建并添加 Document 对象"""
        content = "\n".join(lines)
        
        # 构建层级上下文路径，例如 "颜色混合 > RGB模型 > 计算公式"
        context_path = " > ".join(heading_stack)
        
        # 构造 Metadata
        metadata = {
            "headings": heading_stack,
            "context": context_path,
            "source_type": "markdown_enhanced"
        }
        
        chunks.append(Document(page_content=content, metadata=metadata))
