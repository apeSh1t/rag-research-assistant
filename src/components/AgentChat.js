import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
  Chip,
  Divider,
  Alert,
  Stack
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import { API_BASE_URL } from '../config';

const AgentChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      // 构建对话上下文（最近3轮对话）
      const context = messages.slice(-6).map(msg => ({
        question: msg.role === 'user' ? msg.content : '',
        answer: msg.role === 'assistant' ? msg.content : ''
      })).filter(item => item.question || item.answer);

      const response = await fetch(`${API_BASE_URL}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          context: context
        })
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        const assistantMessage = {
          role: 'assistant',
          content: data.data.answer || '抱歉，我无法生成回答。',
          reasoning: data.data.reasoning || [],
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.message || '请求失败');
      }
    } catch (err) {
      console.error('Agent chat error:', err);
      setError(err.message || '智能问答服务暂时不可用');
      
      // 添加错误消息
      const errorMessage = {
        role: 'assistant',
        content: `抱歉，发生了错误：${err.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ maxWidth: 900, margin: 'auto', mt: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SmartToyIcon sx={{ fontSize: 32, color: 'primary.main', mr: 1 }} />
          <Typography variant="h5" component="h2">
            智能问答助手
          </Typography>
          <Chip 
            label="AI Powered" 
            color="primary" 
            size="small" 
            sx={{ ml: 2 }} 
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Instructions */}
        {messages.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            你好！我是智能研究助手。你可以向我提问关于已上传文档的任何问题，我会基于知识库为你提供详细的解答。
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Messages */}
        <Box
          sx={{
            height: 500,
            overflowY: 'auto',
            mb: 2,
            p: 2,
            backgroundColor: '#f5f5f5',
            borderRadius: 2
          }}
        >
          {messages.length === 0 ? (
            <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 10 }}>
              开始对话吧...
            </Typography>
          ) : (
            <Stack spacing={2}>
              {messages.map((msg, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      maxWidth: '75%',
                      backgroundColor: msg.role === 'user' ? 'primary.light' : 
                                     msg.isError ? '#ffebee' : 'white',
                      color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {msg.role === 'user' ? (
                        <PersonIcon sx={{ fontSize: 20, mr: 1 }} />
                      ) : (
                        <SmartToyIcon sx={{ fontSize: 20, mr: 1, color: msg.isError ? 'error.main' : 'primary.main' }} />
                      )}
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        {msg.role === 'user' ? '你' : 'AI 助手'}
                      </Typography>
                    </Box>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Typography>
                    {msg.reasoning && msg.reasoning.length > 0 && (
                      <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #e0e0e0' }}>
                        <Typography variant="caption" color="text.secondary">
                          推理步骤: {msg.reasoning.length} 步
                        </Typography>
                      </Box>
                    )}
                  </Paper>
                </Box>
              ))}
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <Paper elevation={1} sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                    <CircularProgress size={20} sx={{ mr: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      AI 正在思考...
                    </Typography>
                  </Paper>
                </Box>
              )}
            </Stack>
          )}
        </Box>

        {/* Input */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入你的问题... (Shift+Enter 换行)"
            disabled={loading}
            variant="outlined"
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            endIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
            sx={{ minWidth: 100 }}
          >
            {loading ? '发送中' : '发送'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default AgentChat;
