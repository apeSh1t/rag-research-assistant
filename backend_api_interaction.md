
# Backend API Interaction

## 1. Document Upload API

**Endpoint:** `/api/upload`

**Method:** `POST`

**Description:**  
Uploads a document (e.g., PDF, Word) to the server for processing. The server processes the document, performs OCR, and extracts text content for further use.

**Request Body (Form-data):**
- `file`: The document file to be uploaded.

**Response:**
```json
{
  "status": "success",
  "message": "File uploaded and processed successfully",
  "data": {
    "paperId": "12345",
    "title": "Sample Paper Title",
    "abstract": "Abstract of the paper"
  }
}
```

---

## 2. Document Parsing API

**Endpoint:** `/api/parse`

**Method:** `POST`

**Description:**  
Processes the uploaded document, extracts text, and organizes it into sections. This is typically done using OCR for scanned documents and NLP for text analysis.

**Request Body (JSON):**
```json
{
  "fileId": "12345"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document parsed successfully",
  "data": {
    "sections": [
      {
        "section": "Introduction",
        "content": "Introduction text here."
      },
      {
        "section": "Methods",
        "content": "Methods section text here."
      }
    ]
  }
}
```

---

## 3. Search Query API

**Endpoint:** `/api/search`

**Method:** `POST`

**Description:**  
Searches for relevant document sections based on a query. Uses vector search for semantic retrieval and metadata filtering.

**Request Body (JSON):**
```json
{
  "query": "machine learning in healthcare"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Search results retrieved successfully",
  "data": [
    {
      "section": "Methods",
      "content": "This paper proposes a method for applying machine learning in healthcare."
    },
    {
      "section": "Results",
      "content": "The experiment shows that machine learning improves diagnosis accuracy in healthcare."
    }
  ]
}
```

---

## 4. Document Retrieval API

**Endpoint:** `/api/retrieve`

**Method:** `GET`

**Description:**  
Retrieves a document's detailed content based on its ID.

**Request Parameters:**
- `paperId`: The ID of the paper to retrieve.

**Response:**
```json
{
  "status": "success",
  "message": "Document retrieved successfully",
  "data": {
    "paperId": "12345",
    "title": "Sample Paper Title",
    "sections": [
      {
        "section": "Introduction",
        "content": "Detailed content of the introduction."
      },
      {
        "section": "Results",
        "content": "Detailed content of the results section."
      }
    ]
  }
}
```

