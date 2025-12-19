# RAG Research Assistant - Backend

FastAPI后端服务，提供文档上传、搜索和检索功能。

## 功能特性

- ✅ 文档上传（支持PDF、Word、TXT、Markdown）
- ✅ 文本自动提取
- ✅ 向量化存储（ChromaDB）
- ✅ 智能搜索（基于RAG）
- ✅ 文档元数据管理（SQLite）
- ✅ RESTful API

## 技术栈

- **Web框架**: FastAPI
- **向量数据库**: ChromaDB
- **元数据存储**: SQLite
- **文档处理**: PyPDF2, python-docx
- **AI模型**: LangChain + OpenAI/Qwen

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 3. 启动服务器

```bash
python main.py
```

或使用uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将运行在: http://localhost:8000

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 1. 上传文档
```http
POST /api/upload
Content-Type: multipart/form-data

file: <文件>
```

### 2. 搜索文档
```http
POST /api/search
Content-Type: application/json

{
  "query": "machine learning in healthcare"
}
```

### 3. 检索文档
```http
GET /api/retrieve?paperId=12345
```

### 4. 解析文档
```http
POST /api/parse
Content-Type: application/json

{
  "fileId": "12345"
}
```

## 项目结构

```
backend/
├── main.py                 # FastAPI应用入口
├── api/
│   ├── models.py          # Pydantic数据模型
│   └── routes/            # API路由
│       ├── upload.py
│       ├── search.py
│       ├── retrieve.py
│       └── parse.py
├── services/
│   ├── database.py        # SQLite数据库服务
│   ├── document_processor.py  # 文档处理
│   └── rag_service.py     # RAG服务封装
├── uploads/               # 上传文件存储
├── data/                  # 数据库文件
└── requirements.txt       # Python依赖
```

## 与前端连接

确保前端React应用配置了正确的API地址：

```javascript
// src/config.js
export const API_BASE_URL = 'http://localhost:8000/api';
```

## 开发提示

1. **文件存储**: 上传的文件保存在 `uploads/` 目录，保持原始格式
2. **元数据**: 文档信息存储在 SQLite 数据库 `data/documents.db`
3. **向量检索**: 使用现有的 `rag single/` 中的ChromaDB
4. **日志**: 查看终端输出了解服务状态

## 故障排除

### 1. 导入错误
确保 `rag single/` 目录在正确位置，且已安装所有依赖。

### 2. 向量库未找到
运行 `rag single/knowledge_base/build_index_en.py` 构建索引。

### 3. CORS错误
检查 `.env` 中的 `CORS_ORIGINS` 配置。

## License

MIT
