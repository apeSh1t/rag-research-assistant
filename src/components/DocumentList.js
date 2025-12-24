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
        setError('无法获取文档列表');
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError(`连接后端失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleDelete = async (paperId) => {
    if (!window.confirm('确定要删除这个文档及其索引吗？')) return;

    try {
      const response = await fetch(`${API_ENDPOINTS.DOCUMENTS}/${paperId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchDocuments();
      } else {
        alert('删除失败');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('删除出错');
    }
  };

  const handleView = (fileName) => {
    // 后端挂载了 /uploads 静态目录
    const url = `${API_BASE_URL.replace('/api', '')}/uploads/${fileName}`;
    window.open(url, '_blank');
  };

  if (loading) return <CircularProgress size={24} />;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" gutterBottom>
        已上传文档列表
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper variant="outlined">
        {documents.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="textSecondary">暂无已上传文档</Typography>
          </Box>
        ) : (
          <List>
            {documents.map((doc, index) => (
              <React.Fragment key={doc.paperId}>
                <ListItem
                  secondaryAction={
                    <Box>
                      <Tooltip title="查看原文">
                        <IconButton edge="end" onClick={() => handleView(doc.title)} sx={{ mr: 1 }}>
                          <VisibilityIcon color="primary" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="删除">
                        <IconButton edge="end" onClick={() => handleDelete(doc.paperId)}>
                          <DeleteIcon color="error" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  }
                >
                  <PictureAsPdfIcon sx={{ mr: 2, color: 'error.main' }} />
                  <ListItemText
                    primary={doc.title}
                    secondary={`${(doc.size / 1024).toFixed(2)} KB`}
                  />
                </ListItem>
                {index < documents.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default DocumentList;
