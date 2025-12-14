// src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import Search from './components/Search';
import DocumentDisplay from './components/DocumentDisplay';

function App() {
  const [documentData, setDocumentData] = useState(null);
  const [documents, setDocuments] = useState([]);

  const handleFileParsed = (parsedData) => {
    setDocumentData(parsedData);
    // Adding parsed document to documents array
    setDocuments((prevDocs) => [...prevDocs, parsedData]);
  };

  return (
    <div className="App">
      <h1>RAG-based Research Assistance System</h1>
      
      <FileUpload onFileParsed={handleFileParsed} />
      {documentData && <DocumentDisplay documentData={documentData} />}
      
      <Search documents={documents} />
    </div>
  );
}

export default App;
