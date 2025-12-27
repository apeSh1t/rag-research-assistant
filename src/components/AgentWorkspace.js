import React, { useState, useEffect } from 'react';
import {
  Box,
  Select,
  MenuItem,
  FormControl,
  Typography,
  CircularProgress
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import ChatIcon from '@mui/icons-material/Chat';
import AgentChat from './AgentChat';
import { API_BASE_URL, API_ENDPOINTS } from '../config';

const AgentWorkspace = ({ chatState, setChatState }) => {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.DOCUMENTS);
      const data = await response.json();
      if (response.ok) {
        setDocuments(data.data || []);
        if (data.data && data.data.length > 0) {
          setSelectedDoc(data.data[0].title);
        }
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPdfUrl = () => {
    if (!selectedDoc) return null;
    return `${API_BASE_URL.replace('/api', '')}/uploads/${selectedDoc}`;
  };

  return (
    <div className="workspace-container">
      {/* Left Panel - PDF Viewer */}
      <div className="workspace-panel">
        <div className="panel-header">
          <DescriptionIcon sx={{ color: 'var(--accent)', fontSize: 20 }} />
          <h3 className="panel-title">Document Viewer</h3>
        </div>
        
        <div className="panel-body" style={{ padding: 0 }}>
          {loading ? (
            <div className="empty-state">
              <CircularProgress sx={{ color: 'var(--accent)' }} />
              <Typography sx={{ mt: 2, color: 'var(--text-muted)' }}>
                Loading documents...
              </Typography>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <DescriptionIcon sx={{ fontSize: 64, color: 'var(--text-muted)', mb: 2 }} />
              <Typography sx={{ color: 'var(--text-muted)' }}>
                No documents available
              </Typography>
              <Typography variant="body2" sx={{ color: 'var(--text-muted)', mt: 1 }}>
                Please upload documents first
              </Typography>
            </div>
          ) : (
            <>
              {/* Document Selector */}
              <Box className="doc-selector" sx={{ p: 2, borderBottom: '1px solid var(--border-color)' }}>
                <FormControl fullWidth size="small">
                  <Select
                    value={selectedDoc}
                    onChange={(e) => setSelectedDoc(e.target.value)}
                    sx={{
                      borderRadius: 'var(--radius-md)',
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: 'var(--border-color)'
                      },
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: 'var(--accent)'
                      }
                    }}
                  >
                    {documents.map((doc) => (
                      <MenuItem key={doc.paperId} value={doc.title}>
                        📄 {doc.title}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              {/* PDF Viewer */}
              {selectedDoc && (
                <iframe
                  src={getPdfUrl()}
                  className="pdf-viewer"
                  title="PDF Viewer"
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* Right Panel - Chat Interface */}
      <div className="workspace-panel">
        <div className="panel-header">
          <ChatIcon sx={{ color: 'var(--accent)', fontSize: 20 }} />
          <h3 className="panel-title">AI Assistant</h3>
        </div>
        
        <div className="panel-body" style={{ padding: 0, display: 'flex', flexDirection: 'column' }}>
          <AgentChat chatState={chatState} setChatState={setChatState} />
        </div>
      </div>
    </div>
  );
};

export default AgentWorkspace;
