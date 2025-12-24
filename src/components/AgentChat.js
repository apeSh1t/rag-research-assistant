import React, { useState, useRef, useEffect } from 'react';
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
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { API_BASE_URL } from '../config';

const AgentChat = ({ chatState, setChatState }) => {
  const { messages, input } = chatState;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  // 调试：监听消息变化
  useEffect(() => {
    console.log('当前消息列表:', messages);
  }, [messages]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const setInput = (newInput) => {
    setChatState(prev => ({ ...prev, input: newInput }));
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const currentInput = input;
    const userMessage = {
      role: 'user',
      content: currentInput,
      timestamp: new Date().toISOString()
    };

    const assistantMessageId = Date.now();
    const initialAssistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      reasoning: [],
      timestamp: new Date().toISOString(),
      isStreaming: true
    };

    // 1. 立即更新所有状态，合并为一个调用以确保同步
    setChatState(prev => ({
      ...prev,
      input: '',
      messages: [...prev.messages, userMessage, initialAssistantMessage]
    }));
    
    setLoading(true);
    setError(null);

    try {
      // 构建上下文
      const context = [...messages, userMessage].slice(-7).map(msg => ({
        question: msg.role === 'user' ? msg.content : '',
        answer: msg.role === 'assistant' ? msg.content : ''
      })).filter(item => item.question || item.answer);

      const response = await fetch(`${API_BASE_URL}/agent/chat_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentInput, context })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        const chunk = decoder.decode(value || new Uint8Array(), { stream: !done });
        buffer += chunk;
        
        const lines = buffer.split('\n');
        buffer = done ? '' : lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            console.log('收到事件:', event.type, event);

            setChatState(prev => {
              const newMessages = [...prev.messages];
              const msgIndex = newMessages.findIndex(m => m.id === assistantMessageId);
              
              if (msgIndex === -1) {
                console.warn('未找到对应的助手消息 ID:', assistantMessageId);
                return prev;
              }

              const msg = { ...newMessages[msgIndex] };
              
              if (event.type === 'thought') {
                // 检查是否已存在相同的思考内容
                const exists = msg.reasoning.some(r => r.thought === event.content);
                if (!exists) {
                  msg.reasoning = [...msg.reasoning, {
                    thought: event.content,
                    tool: event.tool || '思考',
                    tool_input: event.tool_input || '',
                    observation: ''
                  }];
                }
              } else if (event.type === 'thought_chunk') {
                // 实时追加到最新的思考步骤中
                if (msg.reasoning.length === 0) {
                  msg.reasoning = [{ thought: event.content, tool: '思考', tool_input: '', observation: '' }];
                } else {
                  const lastStep = { ...msg.reasoning[msg.reasoning.length - 1] };
                  lastStep.thought = (lastStep.thought || '') + event.content;
                  msg.reasoning[msg.reasoning.length - 1] = lastStep;
                }
              } else if (event.type === 'answer_chunk') {
                // 实时追加回答内容
                msg.content = (msg.content || '') + event.content;
              } else if (event.type === 'observation') {
                if (msg.reasoning.length > 0) {
                  const lastStep = { ...msg.reasoning[msg.reasoning.length - 1] };
                  lastStep.observation = event.content;
                  msg.reasoning[msg.reasoning.length - 1] = lastStep;
                }
              } else if (event.type === 'final_answer') {
                msg.content = event.content;
                msg.isStreaming = false;
              } else if (event.type === 'error') {
                msg.content = `错误: ${event.content}`;
                msg.isError = true;
                msg.isStreaming = false;
              }

              newMessages[msgIndex] = msg;
              return { ...prev, messages: newMessages };
            });
          } catch (e) {
            console.error('解析 JSON 失败:', e);
          }
        }
        if (done) break;
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message);
      setChatState(prev => {
        const newMessages = [...prev.messages];
        const msgIndex = newMessages.findIndex(m => m.id === assistantMessageId);
        if (msgIndex !== -1) {
          newMessages[msgIndex] = {
            ...newMessages[msgIndex],
            content: `抱歉，发生了错误：${err.message}`,
            isError: true,
            isStreaming: false
          };
        }
        return { ...prev, messages: newMessages };
      });
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
            label="Agent Mode" 
            color="secondary" 
            size="small" 
            sx={{ ml: 2 }} 
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Instructions */}
        {messages.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            你好！我是智能研究助手。我不仅能回答问题，还能自主思考并调用工具查询知识库。
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
          ref={scrollRef}
          sx={{
            height: 550,
            overflowY: 'auto',
            mb: 2,
            p: 2,
            backgroundColor: '#f8f9fa',
            borderRadius: 2,
            border: '1px solid #e9ecef'
          }}
        >
          {messages.length === 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10, opacity: 0.5 }}>
              <PsychologyIcon sx={{ fontSize: 64, mb: 2 }} />
              <Typography variant="body1">
                准备好开始深度思考了吗？
              </Typography>
            </Box>
          ) : (
            <Stack spacing={3}>
              {messages.map((msg, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5, px: 1 }}>
                    {msg.role === 'user' ? (
                      <PersonIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    ) : (
                      <SmartToyIcon sx={{ fontSize: 16, mr: 0.5, color: 'primary.main' }} />
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                      {msg.role === 'user' ? '你' : 'AI 助手'}
                    </Typography>
                  </Box>
                  
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      maxWidth: '85%',
                      backgroundColor: msg.role === 'user' ? 'primary.main' : 'white',
                      color: msg.role === 'user' ? 'white' : 'text.primary',
                      borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                      border: msg.role === 'user' ? 'none' : '1px solid #dee2e6',
                      boxShadow: msg.role === 'user' ? '0 4px 12px rgba(25, 118, 210, 0.2)' : '0 2px 8px rgba(0,0,0,0.05)'
                    }}
                  >
                    {/* 推理步骤展示 - 移到回答上方 */}
                    {msg.role === 'assistant' && msg.reasoning && msg.reasoning.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Accordion 
                          variant="outlined" 
                          sx={{ 
                            bgcolor: '#f8f9fa', 
                            border: '1px solid #e9ecef',
                            borderRadius: '12px !important',
                            overflow: 'hidden',
                            '&:before': { display: 'none' }
                          }}
                          defaultExpanded={msg.isStreaming}
                        >
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <PsychologyIcon sx={{ fontSize: 18, mr: 1, color: 'secondary.main' }} />
                              <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'secondary.main', letterSpacing: 0.5 }}>
                                {msg.isStreaming ? 'AGENT 正在思考...' : `思考路径 (${msg.reasoning.length} 步)`}
                              </Typography>
                              {msg.isStreaming && <CircularProgress size={12} sx={{ ml: 1 }} color="secondary" />}
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails sx={{ p: 1.5, bgcolor: '#ffffff' }}>
                            <Stack spacing={1.5}>
                              {msg.reasoning.map((step, sIdx) => (
                                <Box key={sIdx} sx={{ p: 1.5, bgcolor: '#f8f9fa', borderRadius: 2, borderLeft: '4px solid #9c27b0' }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: '#9c27b0' }}>
                                      步骤 {sIdx + 1}: {step.tool || '思考'}
                                    </Typography>
                                  </Box>
                                  <Typography variant="caption" display="block" sx={{ color: 'text.primary', mb: 1, lineHeight: 1.5 }}>
                                    {step.thought ? step.thought.replace('Thought:', '').split('Action:')[0].trim() : '正在思考...'}
                                  </Typography>
                                  {step.tool_input && (
                                    <Box sx={{ mb: 1 }}>
                                      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 'bold', fontSize: '0.65rem' }}>输入参数:</Typography>
                                      <Typography variant="caption" display="block" sx={{ bgcolor: '#fff', p: 0.5, borderRadius: 1, border: '1px solid #eee', fontFamily: 'monospace' }}>
                                        {typeof step.tool_input === 'string' ? step.tool_input : JSON.stringify(step.tool_input)}
                                      </Typography>
                                    </Box>
                                  )}
                                  {step.observation ? (
                                    <Box>
                                      <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 'bold', fontSize: '0.65rem' }}>观察结果:</Typography>
                                      <Typography variant="caption" display="block" sx={{ color: 'text.secondary', fontSize: '0.7rem', bgcolor: '#f0fdf4', p: 0.5, borderRadius: 1 }}>
                                        {step.observation.length > 200 ? step.observation.substring(0, 200) + '...' : step.observation}
                                      </Typography>
                                    </Box>
                                  ) : (
                                    msg.isStreaming && sIdx === msg.reasoning.length - 1 && (
                                      <Typography variant="caption" display="block" sx={{ color: 'text.disabled', fontStyle: 'italic' }}>
                                        等待结果...
                                      </Typography>
                                    )
                                  )}
                                </Box>
                              ))}
                            </Stack>
                          </AccordionDetails>
                        </Accordion>
                      </Box>
                    )}

                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                      {msg.content || (msg.isStreaming ? '' : (msg.isError ? '' : 'Agent 未返回具体答案'))}
                    </Typography>
                  </Paper>
                </Box>
              ))}
              {loading && !messages.some(m => m.isStreaming) && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5, px: 1 }}>
                      <SmartToyIcon sx={{ fontSize: 16, mr: 0.5, color: 'primary.main' }} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                        AI 助手
                      </Typography>
                    </Box>
                    <Paper elevation={0} sx={{ p: 2, display: 'flex', alignItems: 'center', borderRadius: '20px 20px 20px 4px', border: '1px solid #dee2e6' }}>
                      <CircularProgress size={16} sx={{ mr: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        正在检索知识库并制定计划...
                      </Typography>
                    </Paper>
                  </Box>
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
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            sx={{ borderRadius: 3, minWidth: 100, px: 3 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default AgentChat;
