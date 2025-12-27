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
    """Hierarchical chunker for Dots OCR JSON documents."""

    MAX_LEVEL = 6  # Maximum heading level to consider

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.hierarchy_types = [DotsChunkType.TITLE, DotsChunkType.SECTION_HEADER]
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

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
        current_chunk_text = ""
        current_chunk_boxes = []
        chunk_idx = 0
        
        # Helper to finalize a chunk
        def finalize_chunk(boxes, text, headings_snapshot):
            nonlocal chunk_idx
            if not text:
                return
            
            # Determine category (majority vote or first box)
            cat = boxes[0].get("category", "Text") if boxes else "Text"
            pg = boxes[0].get("page_no", 0) if boxes else 0
            
            parsed_chunks[chunk_idx] = DotsChunk(
                chunk_idx=chunk_idx,
                text=text,
                category=cat,
                page_no=pg,
                headings=list(headings_snapshot.values()) # Store heading IDs
            )
            chunk_idx += 1

        for i, box in enumerate(sorted_boxes):
            text = box.get("text", "").strip()
            if not text:
                continue

            category = box.get("category", "Text")
            
            # Handle Headings
            if category in [t.value for t in self.hierarchy_types] or text.startswith("#"):
                # If we have accumulated text, finalize it before the new header
                if current_chunk_text:
                    finalize_chunk(current_chunk_boxes, current_chunk_text, heading_by_level.copy())
                    current_chunk_text = ""
                    current_chunk_boxes = []

                # Process this header
                level = self._get_level(text)
                
                # Create a chunk for the header itself
                header_chunk_idx = chunk_idx
                parsed_chunks[header_chunk_idx] = DotsChunk(
                    chunk_idx=header_chunk_idx,
                    text=text,
                    category=category,
                    page_no=box.get("page_no", 0),
                    headings=list(heading_by_level.values()) # Parent headings
                )
                chunk_idx += 1
                
                # Update hierarchy context
                # Remove deeper levels
                keys_to_remove = [k for k in heading_by_level if k >= level]
                for k in keys_to_remove:
                    del heading_by_level[k]
                heading_by_level[level] = header_chunk_idx
                
                continue

            # Handle Normal Text
            # Check size limit
            if len(current_chunk_text) + len(text) + 1 > self.chunk_size and current_chunk_text:
                finalize_chunk(current_chunk_boxes, current_chunk_text, heading_by_level.copy())
                # Implement overlap (simplified: keep last box if small enough)
                # For now, just clear
                current_chunk_text = ""
                current_chunk_boxes = []
            
            current_chunk_text += (" " if current_chunk_text else "") + text
            current_chunk_boxes.append(box)
            
        # Finalize last chunk
        if current_chunk_text:
            finalize_chunk(current_chunk_boxes, current_chunk_text, heading_by_level.copy())
            
        return parsed_chunks

# --- From enhanced_rag_system.py ---

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
            
            # Add category
            # context_parts.append(f"Category: {chunk.category}")
            
            # Add hierarchical context
            if chunk.headings:
                heading_texts = []
                for heading_id in chunk.headings:
                    if heading_id in chunks:
                        heading_texts.append(chunks[heading_id].text)
                if heading_texts:
                    context_parts.append(f"Context: {' > '.join(heading_texts)}")
            
            # Add the main text
            context_parts.append(f"Content: {chunk.text}")
            
            # Combine all parts for embedding
            full_context = "\n".join(context_parts)
            
            # Metadata
            metadata = {
                "chunk_id": int(chunk.chunk_idx),
                "category": chunk.category,
                "page_no": int(chunk.page_no),
                "source": source_file,
                "original_text": chunk.text, # Store original text for display
                "context_str": " > ".join([chunks[h].text for h in chunk.headings if h in chunks])
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
    """Converts PDF to the JSON structure expected by DotsHierarchicalChunker"""
    
    @staticmethod
    def process(file_path: str) -> List[Dict[str, Any]]:
        import pypdf
        
        json_doc = []
        reader = pypdf.PdfReader(file_path)
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            layout_info = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Heuristic for headers:
                # 1. Starts with # (Markdown style)
                # 2. Short line (<= 50 chars) and doesn't end with punctuation (roughly)
                # 3. All caps
                
                category = "Text"
                processed_text = line
                
                is_header = False
                if line.startswith('#'):
                    is_header = True
                    category = "Section-header"
                elif len(line) < 50 and not line.endswith(('.', ',', ';')):
                    # Potential header
                    # If all caps, likely header
                    if line.isupper():
                        is_header = True
                        category = "Section-header"
                        # Add # for the chunker to recognize it
                        processed_text = f"# {line}"
                    # If it looks like "1. Introduction", likely header
                    elif re.match(r'^\d+\.?\s+[A-Z]', line):
                        is_header = True
                        category = "Section-header"
                        processed_text = f"# {line}"
                
                layout_info.append({
                    "text": processed_text,
                    "category": category,
                    "page_no": i + 1
                })
            
            json_doc.append({
                "page_no": i + 1,
                "full_layout_info": layout_info
            })
            
        return json_doc
