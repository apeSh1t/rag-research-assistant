import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress, 
  Alert,
  Stack
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { API_ENDPOINTS } from '../config';

const FileUpload = ({ onFileParsed }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });

  const handleFileChange = (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setStatus({ type: 'info', message: `Selected: ${uploadedFile.name}` });
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus({ type: 'error', message: 'Please select a file first' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'info', message: 'Uploading and indexing document...' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(API_ENDPOINTS.UPLOAD, {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();

      if (response.ok) {
        setStatus({ 
          type: 'success', 
          message: `Success! Indexed ${result.data.chunks || 0} knowledge chunks.` 
        });
        setFile(null);
        // 触发父组件刷新列表
        if (onFileParsed) {
          onFileParsed(result.data);
        }
      } else {
        setStatus({ 
          type: 'error', 
          message: result.detail || 'Upload failed, please check backend logs' 
        });
      }
    } catch (error) {
      console.error('Upload error details:', error);
      setStatus({ 
        type: 'error', 
        message: `Network error: ${error.message}. Request URL: ${API_ENDPOINTS.UPLOAD}. Please check if backend is running and CORS is enabled.` 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <CloudUploadIcon sx={{ color: 'var(--accent)' }} />
        <h3 className="card-title">Upload Document</h3>
      </div>
      
      <div className="card-body">
        <Typography variant="body2" sx={{ color: 'var(--text-secondary)', mb: 3 }}>
          Supported formats: PDF, DOCX, TXT, MD
        </Typography>

        <Box sx={{ my: 2 }}>
          <input
            accept=".pdf,.docx,.txt,.md"
            style={{ display: 'none' }}
            id="raised-button-file"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="raised-button-file">
            <Button 
              variant="outlined" 
              component="span" 
              startIcon={<CloudUploadIcon />}
              disabled={loading}
              sx={{
                borderRadius: 'var(--radius-md)',
                borderColor: 'var(--accent)',
                color: 'var(--accent)',
                '&:hover': {
                  borderColor: 'var(--accent-hover)',
                  bgcolor: 'rgba(99, 102, 241, 0.05)'
                }
              }}
            >
              Choose File
            </Button>
          </label>
        </Box>

        {file && (
          <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
            Ready to upload: {file.name}
          </Typography>
        )}

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || loading}
          className="btn-primary"
          sx={{ minWidth: 150 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Start Upload'}
        </Button>

        {status.message && (
          <Alert severity={status.type} sx={{ width: '100%', mt: 2 }}>
            {status.message}
          </Alert>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
