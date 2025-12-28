import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from enum import Enum
try:
    from langchain.schema import Document
except Exception:
    Document = None

# --- From run_chunker_2.py ---

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
    """Hierarchical chunker for Dots OCR JSON documents (aligned with enhanced_rag_system/run_chunker_2.py)."""

    MAX_LEVEL = 6  # Maximum heading level to consider

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        # chunk_size/overlap kept for backward compatibility; not used in this implementation
        self.hierarchy_types = [DotsChunkType.TITLE, DotsChunkType.SECTION_HEADER]

    def _get_level(self, text: str) -> int:
        """Get the heading level from the text."""
        level = 0
        stripped_text = text.lstrip()
        while stripped_text.startswith("#"):
            level += 1
            stripped_text = stripped_text[1:].lstrip()

        if level == 0:
            return 1
        if level > self.MAX_LEVEL:
            return self.MAX_LEVEL
        return level

    def chunk(self, json_doc: List[Dict[str, Any]]) -> Dict[int, DotsChunk]:
        """
        Chunk a Dots OCR document while maintaining hierarchical context.
        Mirrors enhanced_rag_system/run_chunker_2.py behavior.
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
                box["page_no"] = page_no
                box["idx"] = len(sorted_boxes)
                sorted_boxes.append(box)

        # Chunk by hierarchy & handle captions for tables/images
        for box in sorted_boxes:
            idx = box.get("idx", -1)
            text = box.get("text", "").strip()
            if not text:
                continue

            category = box.get("category", "Text")
            page_no = box.get("page_no", 0)

            def _get_caption() -> Optional[Any]:
                previous_box = sorted_boxes[idx - 1] if idx > 0 else None
                next_box = sorted_boxes[idx + 1] if idx < len(sorted_boxes) - 1 else None
                if previous_box and previous_box.get("category") == DotsChunkType.CAPTION.value and (idx - 1) not in used_captions:
                    used_captions.add(idx - 1)
                    return previous_box
                if next_box and next_box.get("category") == DotsChunkType.CAPTION.value and (idx + 1) not in used_captions:
                    used_captions.add(idx + 1)
                    return next_box
                return None

            def _get_headers_and_register() -> List[int]:
                if not header_boxes:
                    return []

                heading_ids = [heading_by_level[k] for k in sorted(heading_by_level.keys())]

                if heading_by_level:
                    deepest_level = max(heading_by_level.keys())
                    parent_idx = heading_by_level[deepest_level]
                    if parent_idx in header_boxes:
                        header_boxes[parent_idx]["children"].append(idx)

                return heading_ids

            caption_block = None

            if category in [DotsChunkType.TITLE.value, DotsChunkType.SECTION_HEADER.value]:
                level = 0
                if category == DotsChunkType.SECTION_HEADER.value:
                    level = self._get_level(text)

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

                heading_by_level[level] = idx
                continue

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
            elif category in [DotsChunkType.PAGE_HEADER.value, DotsChunkType.PAGE_FOOTER.value]:
                pass
            else:
                pass

            heading_ids = _get_headers_and_register()

            caption = caption_block.get("text") if caption_block else None

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
            category = DotsChunkType.SECTION_HEADER.value if header_info["level"] > 0 else DotsChunkType.TITLE.value
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

# --- Vector Store (FAISS-backed) ---

class EnhancedVectorStore:
    """Enhanced vector store backed by FAISS (cosine) with metadata sidecar."""

    def __init__(self, persist_directory: str, collection_name: str = "document_chunks"):
        # collection_name kept for compatibility; not used in FAISS persistence
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.persist_directory / f"{collection_name}.faiss"
        self.meta_path = self.persist_directory / f"{collection_name}_meta.json"

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index: Optional[faiss.Index] = None
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

        self._load()

    def _load(self):
        """Load FAISS index and metadata if present."""
        if self.index_path.exists() and self.meta_path.exists():
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index = faiss.read_index(self.index_path.as_posix())
            with open(self.meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.documents = meta.get("documents", [])
            self.metadatas = meta.get("metadatas", [])
            self.ids = meta.get("ids", [])
        else:
            self.index = None
            self.documents = []
            self.metadatas = []
            self.ids = []

    def _persist(self):
        """Persist FAISS index and metadata."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, self.index_path.as_posix())
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "documents": self.documents,
                "metadatas": self.metadatas,
                "ids": self.ids,
            }, f, ensure_ascii=False, indent=2)

    def add_chunks(self, chunks: Dict[int, DotsChunk], source_file: str = ""):
        """Add chunks to the vector store with enhanced context preservation"""
        print(f"  [EnhancedVectorStore] Received {len(chunks)} chunks, preparing to process...")
        documents = []
        ids = []
        metadatas = []
        
        for chunk_id, chunk in chunks.items():
            # Prepare document content with enhanced context
            context_parts = []

            # Category
            context_parts.append(f"Category: {chunk.category}")

            # Hierarchical context
            heading_texts = []
            if chunk.headings:
                for heading_id in chunk.headings:
                    if heading_id in chunks:
                        heading_texts.append(chunks[heading_id].text[:100])
            if heading_texts:
                context_parts.append(f"Hierarchical Context: {' > '.join(heading_texts)}")

            # Caption
            if getattr(chunk, "caption", None):
                context_parts.append(f"Caption: {chunk.caption}")

            # Main content
            context_parts.append(f"Content: {chunk.text}")

            full_context = "\n".join(context_parts)

            metadata = {
                "chunk_id": int(chunk.chunk_idx),
                "category": chunk.category if chunk.category is not None else "",
                "page_no": int(chunk.page_no) if chunk.page_no is not None else 0,
                "source": source_file,
                # Preserve both ids and resolved heading texts for downstream clarity
                "headings_ids": json.dumps(chunk.headings) if chunk.headings is not None else "[]",
                "headings": json.dumps(heading_texts) if heading_texts else "[]",
                "caption": chunk.caption if getattr(chunk, "caption", None) else "",
                "children": json.dumps(chunk.children) if getattr(chunk, "children", None) else "",
                "original_text": chunk.text,
                "context_str": " > ".join(heading_texts)
            }

            documents.append(full_context)
            ids.append(f"{source_file}_chunk_{chunk_id}")
            metadatas.append(metadata)
        
        if documents:
            print(f"  [EnhancedVectorStore] Generating Embeddings (Document count: {len(documents)})...")
            try:
                # 分批处理，减小单次写入压力
                batch_size = 5
                total_docs = len(documents)
                total_batches = (total_docs + batch_size - 1) // batch_size
                
                for i in range(0, total_docs, batch_size):
                    end_idx = min(i + batch_size, total_docs)
                    batch_no = i // batch_size + 1
                    print(f"  [EnhancedVectorStore] Processing batch {batch_no}/{total_batches} (Documents {i+1}-{end_idx})...")
                    
                    batch_docs = documents[i:end_idx]
                    batch_ids = ids[i:end_idx]
                    batch_metadatas = metadatas[i:end_idx]
                    
                    try:
                        print("    [EnhancedVectorStore] Starting batch Embedding calculation...")
                        batch_embeddings = self.embedding_model.encode(batch_docs)
                        # Normalize for cosine similarity
                        batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)

                        # Initialize index lazily with correct dim
                        if self.index is None:
                            dim = batch_embeddings.shape[1]
                            self.index = faiss.IndexFlatIP(dim)

                        # Append to in-memory stores
                        self.documents.extend(batch_docs)
                        self.metadatas.extend(batch_metadatas)
                        self.ids.extend(batch_ids)

                        # Add to index
                        self.index.add(batch_embeddings.astype('float32'))
                        print(f"    [EnhancedVectorStore] Batch {batch_no} written successfully.")
                    except Exception as e:
                        import traceback
                        print(f"    [EnhancedVectorStore] Batch {batch_no} write failed: {e}")
                        traceback.print_exc()
                        raise e
                
                # Persist after all batches to avoid partial writes
                self._persist()
                print(f"  [EnhancedVectorStore] All {total_docs} chunks successfully written to vector store.")
            except Exception as e:
                print(f"  [EnhancedVectorStore] Write failed: {e}")
                raise e
        else:
            print("  [EnhancedVectorStore] No documents generated, skipping write.")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks based on query with full information"""
        if self.index is None or not self.ids:
            return []

        query_embedding = self.embedding_model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        scores, idxs = self.index.search(query_embedding.astype('float32'), top_k)

        formatted_results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self.ids):
                continue
            formatted_results.append({
                "id": self.ids[idx],
                "text": self.metadatas[idx].get("original_text", ""),
                "metadata": self.metadatas[idx],
                "score": float(score),
                "full_doc": self.documents[idx]
            })
        return formatted_results

    def retrieve_structured(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Structured retrieval mirroring run_chunker_2 style (chunk_info with hierarchy)."""
        raw = self.retrieve(query, top_k)
        structured = []
        for rank, item in enumerate(raw, 1):
            meta = item.get("metadata", {})
            headings = []
            try:
                headings = json.loads(meta.get("headings", "[]"))
            except Exception:
                headings = meta.get("headings", []) or []

            # Prefer resolved heading texts if present
            try:
                resolved_headings = json.loads(meta.get("headings", "[]"))
            except Exception:
                resolved_headings = headings

            try:
                heading_ids = json.loads(meta.get("headings_ids", "[]"))
            except Exception:
                heading_ids = []

            structured.append({
                "rank": rank,
                "id": item.get("id"),
                "page_no": meta.get("page_no", 0),
                "category": meta.get("category", ""),
                "score": item.get("score", 0.0),
                "headings_count": len(resolved_headings) if isinstance(resolved_headings, list) else 0,
                "headings": resolved_headings,
                "headings_ids": heading_ids,
                "caption": meta.get("caption", ""),
                "children": meta.get("children", ""),
                "source": meta.get("source", ""),
                "text": meta.get("original_text", ""),
                "context": meta.get("context_str", ""),
            })
        return structured

    # LangChain-style interface for existing routes
    def similarity_search_with_score(self, query: str, k: int = 5):
        """Return list of (Document, score) pairs; score is inner product (higher=better)."""
        if self.index is None or not self.ids:
            return []

        query_embedding = self.embedding_model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        scores, idxs = self.index.search(query_embedding.astype('float32'), k)

        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self.ids):
                continue
            meta = dict(self.metadatas[idx]) if isinstance(self.metadatas[idx], dict) else {}
            # Provide a title fallback for callers expecting it
            meta.setdefault("title", meta.get("source", ""))
            content = meta.get("original_text", "")
            if Document:
                doc = Document(page_content=content, metadata=meta)
            else:
                doc = type("Doc", (), {"page_content": content, "metadata": meta})()
            results.append((doc, float(score)))
        return results

    def delete_document(self, source_file: str):
        """Delete all chunks belonging to a source file"""
        self.delete(where={"source": source_file})

    # Thin wrappers used by KnowledgeBase for listing / deletion with filters
    def get(self, where: Optional[Dict[str, Any]] = None):
        where = where or {}
        matched = []
        matched_ids = []
        matched_docs = []
        for i, meta in enumerate(self.metadatas):
            if all(meta.get(k) == v for k, v in where.items()):
                matched.append(meta)
                matched_ids.append(self.ids[i])
                matched_docs.append(self.documents[i])
        return {"ids": matched_ids, "metadatas": matched, "documents": matched_docs}

    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
        if self.index is None:
            return
        to_delete = set(ids or [])
        if where:
            for i, meta in enumerate(self.metadatas):
                if all(meta.get(k) == v for k, v in where.items()):
                    to_delete.add(self.ids[i])

        if not to_delete:
            return

        # Rebuild index without the deleted ids
        keep_docs = []
        keep_meta = []
        keep_ids = []
        keep_embs = []
        for i, id_val in enumerate(self.ids):
            if id_val in to_delete:
                continue
            keep_docs.append(self.documents[i])
            keep_meta.append(self.metadatas[i])
            keep_ids.append(id_val)
            keep_embs.append(self.embedding_model.encode([self.documents[i]])[0])

        if keep_embs:
            embs = np.vstack(keep_embs)
            embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
            dim = embs.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(embs.astype('float32'))
        else:
            self.index = None

        self.documents = keep_docs
        self.metadatas = keep_meta
        self.ids = keep_ids
        self._persist()

# --- PDF Processor ---

class PDFProcessor:
    """Converts PDF to the JSON structure expected by DotsHierarchicalChunker using PyMuPDF (fitz)"""
    
    @staticmethod
    def _get_font_histogram(doc) -> List[tuple]:
        """Statistics of font sizes across the document"""
        font_sizes = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            font_sizes.append(round(s["size"], 1))
        if not font_sizes:
            return []
        return sorted(list(set(font_sizes)), reverse=True)

    @staticmethod
    def process(file_path: str) -> List[Dict[str, Any]]:
        try:
            import fitz
        except ImportError:
            print("PyMuPDF (fitz) not found, falling back to pypdf...")
            # Fallback to original pypdf implementation if fitz is missing
            import pypdf
            json_doc = []
            reader = pypdf.PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text: continue
                lines = text.split('\n')
                layout_info = []
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    category = "Text"
                    processed_text = line
                    if line.startswith('#'):
                        category = "Section-header"
                    elif len(line) < 50 and not line.endswith(('.', ',', ';')):
                        if line.isupper() or re.match(r'^\d+\.?\s+[A-Z]', line):
                            category = "Section-header"
                            processed_text = f"# {line}"
                    layout_info.append({"text": processed_text, "category": category, "page_no": i + 1})
                json_doc.append({"page_no": i + 1, "full_layout_info": layout_info})
            return json_doc

        doc = fitz.open(file_path)
        json_doc = []
        
        # Get font histogram to determine header sizes
        sorted_sizes = PDFProcessor._get_font_histogram(doc)
        
        # Heuristic: 
        # Largest size -> Title
        # 2nd/3rd largest -> Section-header
        title_size = sorted_sizes[0] if sorted_sizes else 0
        h1_size = sorted_sizes[1] if len(sorted_sizes) > 1 else 0
        h2_size = sorted_sizes[2] if len(sorted_sizes) > 2 else 0
        
        for page_num, page in enumerate(doc):
            page_data = {
                "page_no": page_num + 1,
                "full_layout_info": []
            }
            
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] != 0: # Ignore non-text blocks
                    continue
                    
                block_text = ""
                min_x0, min_y0, max_x1, max_y1 = float('inf'), float('inf'), float('-inf'), float('-inf')

                for line in block["lines"]:
                    line_text = ""
                    line_min_x0, line_min_y0, line_max_x1, line_max_y1 = float('inf'), float('inf'), float('-inf'), float('-inf')

                    for span in line["spans"]:
                        text = span.get("text", "")
                        if not text.strip() and not block_text:
                            continue

                        bbox = span.get("bbox", [0, 0, 0, 0])
                        line_min_x0 = min(line_min_x0, bbox[0])
                        line_min_y0 = min(line_min_y0, bbox[1])
                        line_max_x1 = max(line_max_x1, bbox[2])
                        line_max_y1 = max(line_max_y1, bbox[3])

                        line_text += text

                    if line_text.strip():
                        if block_text:
                            block_text += "\n"
                        block_text += line_text.strip()

                    if line_min_x0 != float('inf'):
                        min_x0 = min(min_x0, line_min_x0)
                        min_y0 = min(min_y0, line_min_y0)
                        max_x1 = max(max_x1, line_max_x1)
                        max_y1 = max(max_y1, line_max_y1)

                if block_text.strip():
                    avg_size = 0
                    size_count = 0
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span.get("text", "").strip():
                                avg_size += span.get("size", 0)
                                size_count += 1
                    if size_count > 0:
                        avg_size = round(avg_size / size_count, 1)

                    category = "Text"
                    processed_text = block_text.strip()

                    if avg_size >= title_size and avg_size > 0:
                        category = "Title"
                    elif avg_size >= h1_size and avg_size > 0:
                        category = "Section-header"
                        processed_text = f"# {block_text.strip()}"
                    elif avg_size >= h2_size and avg_size > 0:
                        category = "Section-header"
                        processed_text = f"## {block_text.strip()}"

                    final_bbox = [min_x0, min_y0, max_x1, max_y1] if min_x0 != float('inf') else [0, 0, 0, 0]

                    page_data["full_layout_info"].append({
                        "text": processed_text,
                        "category": category,
                        "page_no": page_num + 1,
                        "bbox": final_bbox
                    })
            
            json_doc.append(page_data)
            
        # Debug: Save the full JSON structure to a file
        if json_doc:
            try:
                # Create debug directory
                debug_dir = Path(__file__).parent.parent / "debug_output"
                debug_dir.mkdir(exist_ok=True)
                
                # Generate filename based on source file
                source_name = Path(file_path).stem
                output_path = debug_dir / f"{source_name}_layout.json"
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(json_doc, f, ensure_ascii=False, indent=2)
                    
                print(f"\n[PDFProcessor] Full layout JSON saved to: {output_path}")
            except Exception as e:
                print(f"[PDFProcessor] Failed to save debug JSON: {e}")

            print("\n[PDFProcessor] Generated JSON Structure (First Page Preview):")
            # Print first page content (limit to first 5 items to avoid spam)
            preview_doc = json_doc[0].copy()
            if len(preview_doc["full_layout_info"]) > 5:
                preview_doc["full_layout_info"] = preview_doc["full_layout_info"][:5] + [{"text": "...", "category": "..."}]
            
            print(json.dumps(preview_doc, ensure_ascii=False, indent=2))
            print(f"[PDFProcessor] Total pages processed: {len(json_doc)}\n")

        return json_doc
