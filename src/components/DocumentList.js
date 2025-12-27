import React, { useEffect, useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Typography,
  Paper,
  Divider,
  Button,
  Tooltip,
  CircularProgress,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { API_BASE_URL, API_ENDPOINTS } from '../config';

const DocumentList = ({ refreshTrigger }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    try {
      setError(null);
      const response = await fetch(API_ENDPOINTS.DOCUMENTS);
      const data = await response.json();
      if (response.ok) {
        setDocuments(data.data);
      } else {
        setError('Unable to fetch document list');
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError(`Failed to connect to backend: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleDelete = async (paperId) => {
    if (!window.confirm('Are you sure you want to delete this document and its index?')) return;

    try {
      const response = await fetch(`${API_ENDPOINTS.DOCUMENTS}/${paperId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchDocuments();
      } else {
        alert('Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Delete error');
    }
  };

  const handleView = (fileName) => {
    // 后端挂载了 /uploads 静态目录
    const url = `${API_BASE_URL.replace('/api', '')}/uploads/${fileName}`;
    window.open(url, '_blank');
  };

  if (loading) return <CircularProgress size={24} />;

  return (
    <div className="card" style={{ marginTop: 24 }}>
      <div className="card-header">
        <PictureAsPdfIcon sx={{ color: 'var(--accent)' }} />
        <h3 className="card-title">Uploaded Documents</h3>
      </div>
      
      <div className="card-body">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {documents.length === 0 ? (
          <div className="empty-state" style={{ padding: 40 }}>
            <PictureAsPdfIcon sx={{ fontSize: 64, color: 'var(--text-muted)', mb: 2 }} />
            <Typography sx={{ color: 'var(--text-muted)' }}>
              No documents uploaded yet
            </Typography>
          </div>
        ) : (
          <div className="doc-list">
            {documents.map((doc) => (
              <div key={doc.paperId} className="doc-item">
                <PictureAsPdfIcon sx={{ fontSize: 24, color: 'var(--accent)', mr: 2 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography sx={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14 }}>
                    {doc.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                    {(doc.size / 1024).toFixed(2)} KB
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="View Document">
                    <IconButton 
                      size="small" 
                      onClick={() => handleView(doc.title)}
                      sx={{ 
                        color: 'var(--accent)',
                        '&:hover': { bgcolor: 'rgba(99, 102, 241, 0.1)' }
                      }}
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton 
                      size="small"
                      onClick={() => handleDelete(doc.paperId)}
                      sx={{ 
                        color: '#ef4444',
                        '&:hover': { bgcolor: 'rgba(239, 68, 68, 0.1)' }
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentList;
