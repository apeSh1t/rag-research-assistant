import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DotsChunkType(Enum):
    """Chunk types for Dots OCR documents."""
    TITLE = "Title"
    SECTION_HEADER = "Section-header"
    TEXT = "Text"
    TABLE = "Table"
    LIST_ITEM = "List-item"
    CAPTION = "Caption"
    FOOTNOTE = "Footnote"
    FORMULA = "Formula"
    PICTURE = "Picture"
    PAGE_HEADER = "Page-header"
    PAGE_FOOTER = "Page-footer"


@dataclass
class DotsChunk:
    """A chunk from Dots OCR processing."""
    chunk_idx: int
    text: str
    category: str
    page_no: int
    headings: List[int]  # Hierarchical context
    caption: Optional[str] = None
    children: Optional[List[int]] = None


class DotsHierarchicalChunker:
    """Hierarchical chunker for Dots OCR JSON documents."""

    MAX_LEVEL = 6  # Maximum heading level to consider

    def __init__(self):
        self.hierarchy_types = [DotsChunkType.TITLE, DotsChunkType.SECTION_HEADER]

    def _get_level(self, text: str) -> int:
        """Get the heading level from the text."""
        level = 0
        stripped_text = text.lstrip()
        while stripped_text.startswith("#"):
            level += 1
            stripped_text = stripped_text[1:].lstrip()

        # If no # found, treat as level 1 (basic section header)
        if level == 0:
            return 1
        # Cap at maximum level
        if level > self.MAX_LEVEL:
            return self.MAX_LEVEL
        return level

    def chunk(self, json_doc: List[Dict[str, Any]]) -> Dict[int, DotsChunk]:
        """
        Chunk a Dots OCR document while maintaining hierarchical context.
        """
        heading_by_level: Dict[int, int] = {}
        used_captions: set = set()
        sorted_boxes: List[Dict[str, Any]] = []
        header_boxes: Dict[int, Dict[str, Any]] = {}
        parsed_chunks: Dict[int, DotsChunk] = {}

        # Collect all boxes sorted by order
        for page in json_doc:
            page_no = page.get("page_no", 0)
            layout_info = page.get("full_layout_info", [])

            for box in layout_info:
                # Add the box to the sorted boxes
                box["page_no"] = page_no
                box["idx"] = len(sorted_boxes)  # Assign a box idx for simplicity
                sorted_boxes.append(box)

        # Chunk by hierachy & handle captions for tables & images
        for box in sorted_boxes:
            idx = box.get("idx", -1)

            text = box.get("text", "").strip()
            if not text:
                continue

            category = box.get("category", "Text")
            page_no = box.get("page_no", 0)

            def _get_caption() -> Optional[Any]:
                """Extract caption from surrounding boxes."""
                previous_box = sorted_boxes[idx - 1] if idx > 0 else None
                next_box = (
                    sorted_boxes[idx + 1] if idx < len(sorted_boxes) - 1 else None
                )
                if (
                        previous_box
                        and previous_box.get("category") == DotsChunkType.CAPTION.value
                        and (idx - 1) not in used_captions
                ):
                    used_captions.add(idx - 1)
                    return previous_box
                elif (
                        next_box
                        and next_box.get("category") == DotsChunkType.CAPTION.value
                        and (idx + 1) not in used_captions
                ):
                    used_captions.add(idx + 1)
                    return next_box
                return None

            def _get_headers_and_register() -> List[int]:
                """Register headers in the chunk."""
                if not header_boxes:
                    return []

                heading_ids = [
                    heading_by_level[k] for k in sorted(heading_by_level.keys())
                ]

                # Add self to the children of its direct parent
                if heading_by_level:
                    # Get the most recent (deepest) heading
                    deepest_level = max(heading_by_level.keys())
                    parent_idx = heading_by_level[deepest_level]
                    if parent_idx in header_boxes:
                        header_boxes[parent_idx]["children"].append(idx)

                return heading_ids

            caption_block = None

            # Heading hierarchy, don't parse immediately
            if category in [
                DotsChunkType.TITLE.value,
                DotsChunkType.SECTION_HEADER.value,
            ]:
                level = 0  # Default to highest priority for titles

                if category == DotsChunkType.SECTION_HEADER.value:
                    level = self._get_level(text)

                # Remove all deeper and same level headings
                keys_to_del = [k for k in heading_by_level if k >= level]
                for k in keys_to_del:
                    heading_by_level.pop(k, None)

                heading_ids = _get_headers_and_register()

                header_boxes[idx] = {
                    "text": text,
                    "level": level,
                    "page_no": page_no,
                    "headers": heading_ids,
                    "children": [],
                }

                # Update heading hierarchy
                heading_by_level[level] = idx
                continue

            # Raw Text and List Items
            elif category in [DotsChunkType.TEXT.value, DotsChunkType.LIST_ITEM.value]:
                pass

            elif category == DotsChunkType.TABLE.value:
                caption_block = _get_caption()

            elif category == DotsChunkType.PICTURE.value:
                caption_block = _get_caption()

            elif category == DotsChunkType.FORMULA.value:
                caption_block = _get_caption()

            elif category == DotsChunkType.FOOTNOTE.value:
                pass

            elif category in [
                DotsChunkType.PAGE_HEADER.value,
                DotsChunkType.PAGE_FOOTER.value,
            ]:
                pass

            else:
                pass

            heading_ids = _get_headers_and_register()

            if caption_block:
                caption = caption_block.get("text", None)
            else:
                caption = None

            chunk = DotsChunk(
                chunk_idx=idx,
                text=text,
                category=category,
                page_no=page_no,
                headings=heading_ids,
                caption=caption,
            )

            parsed_chunks[idx] = chunk

        # Add headers to parsed_chunks
        for header_idx, header_info in header_boxes.items():
            category = (
                DotsChunkType.SECTION_HEADER.value
                if header_info["level"] > 0
                else DotsChunkType.TITLE.value
            )

            if header_info["children"] == []:
                category = DotsChunkType.TEXT.value

            chunk = DotsChunk(
                chunk_idx=header_idx,
                text=header_info["text"],
                category=category,
                page_no=header_info["page_no"],
                headings=header_info["headers"],
                caption=None,
                children=header_info["children"],
            )

            parsed_chunks[header_idx] = chunk

        return parsed_chunks


def print_tree(chunks: Dict[int, DotsChunk]):
    """简单可视化 Chunk 树结构"""
    print("\n=== Chunk Hierarchy ===\n")

    # 按照索引排序输出
    sorted_ids = sorted(chunks.keys())

    for idx in sorted_ids:
        chunk = chunks[idx]

        # 获取父级标题的文本（用于展示Context）
        parent_titles = []
        for h_id in chunk.headings:
            if h_id in chunks:
                # 截取标题前10个字
                parent_titles.append(chunks[h_id].text[:10] + "...")

        context_str = " > ".join(parent_titles) if parent_titles else "ROOT"

        # 格式化输出
        indent = "  " * len(chunk.headings)
        marker = "📄" if chunk.category == "Text" else "🏷️"
        if chunk.category == "Section-header" or chunk.category == "Title":
            marker = "📑"

        print(f"{indent}{marker} [{chunk.category}] (ID:{idx})")
        print(f"{indent}   Text: {chunk.text[:50]}...")
        print(f"{indent}   Context: {context_str}")
        if hasattr(chunk, 'children') and chunk.children:
            print(f"{indent}   Children IDs: {chunk.children}")
        print("-" * 40)


def save_chunks_to_json(chunks: Dict[int, DotsChunk], output_path: str):
    """将chunks保存到JSON文件"""
    # 转换chunks为可序列化的格式
    serializable_chunks = {}
    for chunk_id, chunk in chunks.items():
        serializable_chunks[chunk_id] = {
            "chunk_idx": chunk.chunk_idx,
            "text": chunk.text,
            "category": chunk.category,
            "page_no": chunk.page_no,
            "headings": chunk.headings,
            "caption": chunk.caption,
            "children": chunk.children if hasattr(chunk, 'children') and chunk.children else None
        }
    
    # 保存到JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"Chunks已保存到 {output_path}")


def load_chunks_from_json(input_path: str) -> Dict[int, DotsChunk]:
    """从JSON文件加载chunks"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换回DotsChunk对象
    chunks = {}
    for chunk_id, chunk_data in data.items():
        chunk_id = int(chunk_id)  # JSON中的键是字符串，需要转换为整数
        chunks[chunk_id] = DotsChunk(
            chunk_idx=chunk_data["chunk_idx"],
            text=chunk_data["text"],
            category=chunk_data["category"],
            page_no=chunk_data["page_no"],
            headings=chunk_data["headings"],
            caption=chunk_data["caption"],
            children=chunk_data["children"]
        )
    
    print(f"从 {input_path} 加载了 {len(chunks)} 个chunks")
    return chunks


def main(json_path: str, output_chunks_path: str = None):
    # 1. 加载模拟的 OCR JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_doc = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_path}。请先运行 mock_ocr_scanner.py 生成数据。")
        return

    # 2. 初始化 Chunker
    chunker = DotsHierarchicalChunker()

    # 3. 执行 Chunk
    print(f"正在处理 {len(json_doc)} 页文档...")
    chunks = chunker.chunk(json_doc)

    # 4. 保存结果到JSON文件（如果指定了输出路径）
    if output_chunks_path:
        save_chunks_to_json(chunks, output_chunks_path)

    # 5. 输出结果
    print(f"处理完成，生成了 {len(chunks)} 个 Chunks。")
    print_tree(chunks)
    
    return chunks


if __name__ == "__main__":
    from mock_ocr_scanner import scan_pdf_to_json

    pdf_file = "sample.pdf"  # 请替换为你的本地 PDF 文件路径
    json_file = "dots_output.json"
    chunks_file = "chunks_output_2.json"  # 新增：chunks保存路径

    # 步骤 1: 扫描 (如果没有 sample.pdf，这里会报错，请确保文件存在)
    scan_pdf_to_json(pdf_file, json_file)

    # 步骤 2: Chunk (使用现有的 json 文件)
    main(json_file, chunks_file)