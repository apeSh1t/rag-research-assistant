# RAG Research Assistant System

A sophisticated Retrieval-Augmented Generation (RAG) system designed for deep research tasks. This system combines a modern React frontend with a powerful Python backend, featuring an autonomous agent capable of hierarchical document understanding, planning, and reasoning.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![React](https://img.shields.io/badge/react-18.0%2B-blue)

## 🌟 Key Features

- **Autonomous Research Agent**: A LangChain-based agent that plans, reasons, and executes multi-step research tasks.
- **Hierarchical Chunking**: Advanced document processing that preserves document structure (headers, sections) for context-aware retrieval.
- **Context-Aware Vector Storage**: Stores semantic context along with content chunks to improve retrieval accuracy for short or ambiguous segments.
- **Split-Screen Interface**: Modern UI with side-by-side PDF viewing and Agent chat/reasoning visualization.
- **Streaming Reasoning**: Real-time visualization of the Agent's thought process (Chain of Thought) and tool usage.

## 🏗️ Architecture

The system consists of three main layers:

1.  **Frontend (React + Material UI)**:
    -   Manages user interaction, PDF rendering, and chat interface.
    -   Visualizes the Agent's reasoning steps via a streaming UI.
2.  **Backend (FastAPI)**:
    -   Exposes REST APIs for document processing, search, and agent interaction.
    -   Handles file uploads and parsing.
3.  **RAG Engine (LangChain + FAISS)**:
    -   **Knowledge Base**: Manages document indexing and retrieval.
    -   **Agent Core**: Executes the ReAct (Reasoning + Acting) loop using LLMs (e.g., Qwen-max).

## 🚀 Technical Implementation Details

### 1. Hierarchical Chunking & Context-Aware Storage
Unlike traditional fixed-size chunking, this system uses a **Hierarchical Chunker** (`DotsHierarchicalChunker`) to preserve the semantic structure of documents.

-   **Structure Recognition**: The system parses PDF/Markdown headers to build a "Context Path" (e.g., `Introduction > Background > Motivation`).
-   **Storage Format**:
    When storing chunks in the FAISS vector database, the context is prepended to the content:
    ```text
    Context: Chapter 1 > Section 1.2 > Methodology
    Content: We employed a transformer-based architecture...
    ```
    This ensures that even small chunks retain their semantic meaning during vector retrieval.

### 2. Vector Database (FAISS)
-   **Engine**: `faiss-cpu` for efficient similarity search.
-   **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions).
-   **Metadata**: Stores original text, source filename, page numbers, and the full context path for UI display.

### 3. Autonomous Agent Workflow
The Agent is built using **LangChain** and follows a planning-execution loop:
1.  **Planning**: Analyzes the user query and breaks it down into sub-tasks.
2.  **Tool Execution**: Calls the `search_knowledge` tool to retrieve information from the FAISS index.
3.  **Reasoning**: Synthesizes retrieved information. If information is missing, it replans and searches again.
4.  **Response**: Streams the final answer along with the reasoning trace to the frontend.

## 🛠️ Environment Setup

### Prerequisites
-   **Node.js** (v16+) and **npm**
-   **Python** (v3.8+)
-   **API Key**: An OpenAI-compatible API key (e.g., DashScope/Qwen).

### 1. Backend Setup

Navigate to the project root (or `backend` folder depending on your structure preference, but based on current workspace, the python scripts are in `backend/` and `rag single/`).

1.  **Install Python Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    pip install -r "rag single/requirements.txt"
    ```
    *Note: Ensure you have `torch`, `faiss-cpu`, `langchain`, `fastapi`, `uvicorn`, etc. installed.*

2.  **Configure Environment Variables**:
    Create a `.env` file in the `backend` directory (or root) with your API keys:
    ```env
    DASHSCOPE_API_KEY=your_api_key_here
    # Or OPENAI_API_KEY if using OpenAI models
    ```

### 2. Frontend Setup

Navigate to the root directory (where `package.json` is located).

1.  **Install Node Dependencies**:
    ```bash
    npm install
    ```

## 🏃‍♂️ Running the Application

### Step 1: Start the Backend Server
The backend entry point is likely in `backend/main.py`.

```bash
# From the root directory
python -m uvicorn backend.main:app --reload --port 8000
```
*Ensure the backend is running on http://localhost:8000*

### Step 2: Start the Frontend Client

```bash
# From the root directory
npm start
```
*The application will open at http://localhost:3000*

## 📂 Project Structure

```
rag-research-system/
├── backend/                # FastAPI Backend
│   ├── api/                # API Routes (chat, search, upload)
│   ├── services/           # Business logic
│   └── main.py             # Server entry point
├── rag single/             # RAG Core Implementation
│   ├── agent.py            # LangChain Agent logic
│   ├── knowledge_base/     # Vector Store & Chunking
│   │   ├── enhanced_system.py # FAISS implementation
│   │   ├── enhanced_chunker.py# Hierarchical chunking
│   │   └── kb.py           # Knowledge Base interface
│   └── chroma_db_en/       # (Legacy/Alternative) Vector Store
├── src/                    # React Frontend
│   ├── components/         # UI Components
│   │   ├── AgentChat.js    # Chat interface with reasoning display
│   │   ├── AgentWorkspace.js # Split-screen layout
│   │   └── ...
│   ├── App.js              # Main App component
│   └── ...
├── public/                 # Static assets
└── package.json            # Frontend dependencies
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
