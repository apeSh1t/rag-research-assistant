import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Optional
import json
from run_chunker import DotsChunk, DotsHierarchicalChunker


class EnhancedVectorStore:
    """Enhanced vector store with flexible chunk storage and retrieval"""
    
    def __init__(self, collection_name: str = "document_chunks"):
        # Initialize chromadb client
        self.client = chromadb.Client()
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Enhanced document chunks collection with full context"}
        )
        
        # Initialize sentence transformer for embedding generation
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_chunks(self, chunks: Dict[int, DotsChunk]):
        """Add chunks to the vector store with enhanced context preservation"""
        documents = []
        ids = []
        metadatas = []
        
        for chunk_id, chunk in chunks.items():
            # Prepare document content with enhanced context
            # Include hierarchical context in the document content
            context_parts = []
            
            # Add category and basic info
            context_parts.append(f"Category: {chunk.category}")
            
            # Add hierarchical context if available
            if chunk.headings:
                heading_texts = []
                for heading_id in chunk.headings:
                    if heading_id in chunks:
                        heading_texts.append(chunks[heading_id].text[:100])  # Limit length for metadata
                if heading_texts:
                    context_parts.append(f"Hierarchical Context: {' > '.join(heading_texts)}")
            
            # Add caption if available
            if chunk.caption:
                context_parts.append(f"Caption: {chunk.caption}")
            
            # Add the main text
            context_parts.append(f"Content: {chunk.text}")
            
            # Combine all parts
            full_context = "\n".join(context_parts)
            
            # Add metadata - convert lists to strings for ChromaDB compatibility and handle None values
            metadata = {
                "chunk_id": int(chunk.chunk_idx),
                "category": chunk.category if chunk.category is not None else "",
                "page_no": int(chunk.page_no) if chunk.page_no is not None else 0,
                "headings": json.dumps(chunk.headings) if chunk.headings is not None else "[]",
                "caption": chunk.caption if chunk.caption is not None else "",
                "text": chunk.text  # Store original text for full retrieval
            }
            
            # If chunk has children, add them to metadata
            if hasattr(chunk, 'children') and chunk.children is not None:
                metadata["children"] = json.dumps(chunk.children)
            
            documents.append(full_context)
            ids.append(f"chunk_{chunk_id}")
            metadatas.append(metadata)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"Added {len(chunks)} chunks to vector store")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks based on query with full information"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results with full information
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "full_text": results["metadatas"][0][i].get("text", "")  # Full original text
            })
        
        return formatted_results


class EnhancedRAGSystem:
    """Enhanced RAG system with better chunk adaptation and complete storage/retrieval functionality"""
    
    def __init__(self, vector_store: EnhancedVectorStore):
        self.vector_store = vector_store
    
    def load_document(self, json_path: str):
        """Load and process a document"""
        # Use existing chunker to process document
        chunker = DotsHierarchicalChunker()
        
        # Load JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            json_doc = json.load(f)
        
        # Chunk the document
        chunks = chunker.chunk(json_doc)
        
        # Add chunks to vector store
        self.vector_store.add_chunks(chunks)
        
        return chunks
    
    def load_chunks_from_file(self, chunks_path: str):
        """Load pre-chunked data from JSON file and add to vector store"""
        # Load chunks from JSON file
        with open(chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert back to DotsChunk objects
        chunks = {}
        for chunk_id, chunk_data in data.items():
            chunk_id = int(chunk_id)  # JSON keys are strings, need to convert to integers
            chunks[chunk_id] = DotsChunk(
                chunk_idx=chunk_data["chunk_idx"],
                text=chunk_data["text"],
                category=chunk_data["category"],
                page_no=chunk_data["page_no"],
                headings=chunk_data["headings"],
                caption=chunk_data["caption"],
                children=chunk_data["children"]
            )
        
        print(f"Loaded {len(chunks)} chunks from {chunks_path}")
        
        # Add chunks to vector store
        self.vector_store.add_chunks(chunks)
        
        return chunks
    
    def answer_query(self, query: str, top_k: int = 5) -> str:
        """Answer a query based on the retrieved chunks with full information"""
        # Retrieve relevant chunks
        relevant_chunks = self.vector_store.retrieve(query, top_k)
        
        if not relevant_chunks:
            return "No relevant information found."
        
        # Build context from retrieved chunks with enhanced hierarchical information
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            # Use the full original text for better context
            content = chunk['full_text']
            
            # Build enhanced context with hierarchical information
            chunk_info = f"[Chunk {i+1}]"
            chunk_info += f" (ID: {chunk['id']}"
            chunk_info += f", Page: {chunk['metadata']['page_no']}"
            chunk_info += f", Category: {chunk['metadata']['category']}"
            chunk_info += f", Distance: {chunk['distance']:.4f}"
            
            # Add hierarchical context information if available
            try:
                headings_list = json.loads(chunk['metadata']['headings'])
                if headings_list:
                    chunk_info += f", Headings Count: {len(headings_list)}"
            except:
                pass
            
            chunk_info += ")"
            context_parts.append(f"{chunk_info}\n{content}")
        
        # Join all context parts
        context = "\n\n---\n\n".join(context_parts)
        
        # Generate answer using the context
        answer = self._generate_answer(query, context)
        
        return answer
    
    def _generate_answer(self, query: str, context: str) -> str:
        """Generate an answer based on query and context with full information"""
        # Return detailed information including the full context
        answer = f"Based on the retrieved information, here's what I found about '{query}':\n\n"
        
        # Include the full context without filtering
        if context.strip():
            answer += context
        else:
            answer += "No relevant context found."
        
        return answer
    
    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Directly search chunks and return brief information"""
        results = self.vector_store.retrieve(query, top_k)
        
        # Simplify the results for easier consumption
        simplified_results = []
        for result in results:
            simplified_results.append({
                "id": result["id"],
                "preview": result["full_text"][:150] + "..." if len(result["full_text"]) > 150 else result["full_text"],
                "category": result["metadata"]["category"],
                "page": result["metadata"]["page_no"],
                "distance": result["distance"]
            })
        
        return simplified_results


def demonstrate_usage():
    """Demonstrate how to use the enhanced RAG system"""
    print("=== Enhanced RAG System Demo ===\n")
    
    # Create vector store and RAG system
    vector_store = EnhancedVectorStore()
    rag_system = EnhancedRAGSystem(vector_store)
    
    # Load pre-processed chunks
    print("1. Loading pre-processed chunks...")
    chunks = rag_system.load_chunks_from_file("chunks_output.json")
    print(f"   Successfully loaded {len(chunks)} chunks\n")
    
    # Example query 1: Search for specific topic
    print("2. Example Query 1: Search for information about 'RAG evaluation'")
    query1 = "RAG evaluation methods"
    results1 = rag_system.search_chunks(query1, top_k=3)
    print(f"   Found {len(results1)} relevant chunks:")
    for i, result in enumerate(results1):
        print(f"   Chunk {i+1}: {result['id']} (Distance: {result['distance']:.4f})")
        print(f"   Preview: {result['preview']}")
    print()
    
    # Example query 2: Use Q&A functionality
    print("3. Example Query 2: Use Q&A functionality")
    query2 = "crowdsourcing in RAG"
    answer2 = rag_system.answer_query(query2, top_k=3)
    print(f"   Query: {query2}")
    print(f"   Answer:\n{answer2}\n")
    
    # Example query 3: Search for specific section
    print("4. Example Query 3: Search for content about 'Abstract'")
    query3 = "abstract of the paper"
    results3 = rag_system.search_chunks(query3, top_k=1)
    if results3:
        print(f"   Found the most relevant chunk: {results3[0]['id']}")
        # Get full content for abstract
        full_results = rag_system.vector_store.retrieve(query3, top_k=1)
        print(f"   Full content:\n{full_results[0]['full_text']}")
    print()
    
    print("=== Demo Completed ===")


if __name__ == "__main__":
    demonstrate_usage()