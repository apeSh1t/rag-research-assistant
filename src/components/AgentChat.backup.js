import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Stack
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { API_BASE_URL } from '../config';

const AgentChat = ({ chatState, setChatState }) => {
  const { messages, input } = chatState;
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

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
      timestamp: new Date().toISOString(),
      isStreaming: true
    };

    setChatState(prev => ({
      ...prev,
      input: '',
      messages: [...prev.messages, userMessage, initialAssistantMessage]
    }));
    
    setLoading(true);

    try {
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

            setChatState(prev => {
              const newMessages = [...prev.messages];
              const msgIndex = newMessages.findIndex(m => m.id === assistantMessageId);
              
              if (msgIndex === -1) return prev;

              const msg = { ...newMessages[msgIndex] };
              
              if (event.type === 'answer_chunk') {
                msg.content = (msg.content || '') + event.content;
              } else if (event.type === 'final_answer') {
                msg.content = event.content;
                msg.isStreaming = false;
              } else if (event.type === 'error') {
                msg.content = `Error: ${event.content}`;
                msg.isError = true;
                msg.isStreaming = false;
              }

              newMessages[msgIndex] = msg;
              return { ...prev, messages: newMessages };
            });
          } catch (e) {
            console.error('JSON parse error:', e);
          }
        }
        if (done) break;
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setChatState(prev => {
        const newMessages = [...prev.messages];
        const msgIndex = newMessages.findIndex(m => m.id === assistantMessageId);
        if (msgIndex !== -1) {
          newMessages[msgIndex] = {
            ...newMessages[msgIndex],
            content: `Sorry, an error occurred: ${err.message}`,
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
    <div className="chat-container">
      {/* Messages */}
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <PsychologyIcon sx={{ fontSize: 64, color: 'var(--text-muted)', mb: 2 }} />
            <Typography sx={{ color: 'var(--text-muted)' }}>
              Ask me anything about your documents
            </Typography>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.role}`}>
                <div className="message-header">
                  {msg.role === 'user' ? (
                    <PersonIcon sx={{ fontSize: 16, color: 'var(--text-secondary)' }} />
                  ) : (
                    <SmartToyIcon sx={{ fontSize: 16, color: 'var(--accent)' }} />
                  )}
                  <span className="message-sender">
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </span>
                </div>
                <div className={`message-bubble ${msg.role}`}>
                  <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                    {msg.content || (msg.isStreaming ? '' : 'No response')}
                  </Typography>
                </div>
              </div>
            ))}
            {loading && !messages.some(m => m.isStreaming) && (
              <div className="chat-message assistant">
                <div className="message-header">
                  <SmartToyIcon sx={{ fontSize: 16, color: 'var(--accent)' }} />
                  <span className="message-sender">AI Assistant</span>
                </div>
                <div className="message-bubble assistant">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" color="text.secondary">
                      Thinking...
                    </Typography>
                  </Box>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask anything... (Shift+Enter for new line)"
            disabled={loading}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 'var(--radius-md)',
                bgcolor: 'white',
                '& fieldset': { borderColor: 'var(--border-color)' },
                '&:hover fieldset': { borderColor: 'var(--accent)' },
                '&.Mui-focused fieldset': { borderColor: 'var(--accent)' }
              }
            }}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            className="btn-primary"
            sx={{ minWidth: 100 }}
          >
            {loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          </Button>
        </Stack>
      </div>
    </div>
  );
};

export default AgentChat;
