// src/components/DocumentDisplay.js
import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Divider, CircularProgress } from '@mui/material';

const DocumentDisplay = ({ documentData: propData, paperId }) => {
  const [documentData, setDocumentData] = useState(propData);

  useEffect(() => {
    if (propData) {
      setDocumentData(propData);
      return;
    }

    const fetchDocument = async () => {
      try {
        const response = await fetch(`/api/retrieve?paperId=${paperId}`);
        const data = await response.json();

        if (response.ok) {
          setDocumentData(data.data);  
        } else {
          console.error('Error retrieving document');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

    if (paperId) {
      fetchDocument();
    }
  }, [paperId, propData]);

  if (!documentData) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress size={24} sx={{ mb: 1 }} />
        <Typography color="textSecondary">正在加载文档内容...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h5" gutterBottom color="primary">
        {documentData.title || '已解析文档内容'}
      </Typography>
      <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f9f9f9' }}>
        {documentData.sections && documentData.sections.map((section, index) => (
          <Box key={index} sx={{ mb: 3 }}>
            <Typography variant="h6" color="secondary" gutterBottom>
              {section.section}
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {section.content}
            </Typography>
            {index < documentData.sections.length - 1 && <Divider sx={{ mt: 2 }} />}
          </Box>
        ))}
      </Paper>
    </Box>
  );
};

export default DocumentDisplay;
