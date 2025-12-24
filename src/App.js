// src/App.js
import React, { useState } from 'react';
import { Box, Container, Tabs, Tab, Typography, Paper } from '@mui/material';
import FileUpload from './components/FileUpload';
import Search from './components/Search';
import DocumentDisplay from './components/DocumentDisplay';
import AgentChat from './components/AgentChat';
import DocumentList from './components/DocumentList';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [documentData, setDocumentData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  const [refreshList, setRefreshList] = useState(0);

  const handleFileParsed = (parsedData) => {
    setDocumentData(parsedData);
    // Adding parsed document to documents array
    setDocuments((prevDocs) => [...prevDocs, parsedData]);
    // Trigger list refresh
    setRefreshList(prev => prev + 1);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <div className="App">
      <Box sx={{ bgcolor: 'primary.main', color: 'white', p: 3, mb: 3 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" component="h1" gutterBottom>
            🔬 RAG Research Assistant
          </Typography>
          <Typography variant="subtitle1">
            智能文档检索与问答系统 - MVP 1.0
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg">
        <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="📤 文档上传" />
            <Tab label="🔍 文档搜索" />
            <Tab label="🤖 智能问答" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <FileUpload onFileParsed={handleFileParsed} />
            <DocumentList refreshTrigger={refreshList} />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Search documents={documents} />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <AgentChat />
          </TabPanel>
        </Paper>
      </Container>
    </div>
  );
}

export default App;
