// src/App.js
import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import Search from './components/Search';
import AgentWorkspace from './components/AgentWorkspace';
import DocumentList from './components/DocumentList';
import './App.css';

// Icon components (using emojis for simplicity)
const UploadIcon = () => <span className="nav-item-icon">📤</span>;
const SearchIcon = () => <span className="nav-item-icon">🔍</span>;
const ChatIcon = () => <span className="nav-item-icon">🤖</span>;

function App() {
  const [documentData, setDocumentData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activeTab, setActiveTab] = useState('upload');
  const [refreshList, setRefreshList] = useState(0);

  // Persistent search state
  const [searchState, setSearchState] = useState({
    query: '',
    results: [],
    searched: false
  });

  // Persistent chat state
  const [chatState, setChatState] = useState({
    messages: [],
    input: ''
  });

  const handleFileParsed = (parsedData) => {
    setDocumentData(parsedData);
    setDocuments((prevDocs) => [...prevDocs, parsedData]);
    setRefreshList(prev => prev + 1);
  };

  const navItems = [
    { id: 'upload', label: 'Upload', icon: UploadIcon },
    { id: 'search', label: 'Search', icon: SearchIcon },
    { id: 'agent', label: 'AI Assistant', icon: ChatIcon }
  ];

  return (
    <div className="App">
      {/* Sidebar Navigation */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title">
            🔬 RAG Research
          </h1>
          <p className="sidebar-subtitle">Intelligent Document Q&A System</p>
        </div>
        
        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <item.icon />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {activeTab === 'upload' && (
          <>
            <FileUpload onFileParsed={handleFileParsed} />
            <DocumentList refreshTrigger={refreshList} />
          </>
        )}

        {activeTab === 'search' && (
          <Search 
            searchState={searchState} 
            setSearchState={setSearchState} 
          />
        )}

        {activeTab === 'agent' && (
          <AgentWorkspace 
            chatState={chatState} 
            setChatState={setChatState} 
          />
        )}
      </div>
    </div>
  );
}

export default App;
