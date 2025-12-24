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
      setStatus({ type: 'info', message: `已选择文件: ${uploadedFile.name}` });
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus({ type: 'error', message: '请先选择一个文件' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'info', message: '正在上传并索引文档，请稍候...' });

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
          message: `成功！已索引 ${result.data.chunks || 0} 个知识片段。` 
        });
        setFile(null);
        // 触发父组件刷新列表
        if (onFileParsed) {
          onFileParsed(result.data);
        }
      } else {
        setStatus({ 
          type: 'error', 
          message: result.detail || '上传失败，请检查后端日志' 
        });
      }
    } catch (error) {
      console.error('Upload error details:', error);
      setStatus({ 
        type: 'error', 
        message: `网络错误: ${error.message}。请求地址: ${API_ENDPOINTS.UPLOAD}。请检查后端是否启动并允许跨域。` 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 3, textAlign: 'center', bgcolor: '#fafafa' }}>
      <Stack spacing={2} alignItems="center">
        <Typography variant="h6" gutterBottom>
          上传新文档到知识库
        </Typography>
        
        <Typography variant="body2" color="textSecondary">
          支持 PDF, DOCX, TXT, MD 格式
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
            >
              选择文件
            </Button>
          </label>
        </Box>

        {file && (
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            待上传: {file.name}
          </Typography>
        )}

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || loading}
          sx={{ minWidth: 150 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : '开始上传'}
        </Button>

        {status.message && (
          <Alert severity={status.type} sx={{ width: '100%', mt: 2 }}>
            {status.message}
          </Alert>
        )}
      </Stack>
    </Paper>
  );
};

export default FileUpload;
