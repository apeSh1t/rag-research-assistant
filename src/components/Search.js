import React, { useState } from 'react';
import { TextField, Button, Box, Typography } from '@mui/material';
import { API_ENDPOINTS } from '../config';

const Search = ({ documents }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const searchDocuments = (query) => {
    if (!Array.isArray(documents)) return [];

    return documents.filter((doc) => doc.content && doc.content.includes(query));
  };

  const handleSearch = async () => {
    if (!query) {
      setResults([]); // 清空结果
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.SEARCH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      const searchData = await response.json();

      if (response.ok) {
        setResults(searchData.data);  // Update the results with the search data
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    }
  };

  return (
    <Box>
      <TextField
        label="Search Documents"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        fullWidth
        sx={{ marginBottom: 2 }}
      />
      <Button variant="contained" onClick={handleSearch} sx={{ marginBottom: 4 }}>
        Search
      </Button>
      <Box>
        {results.length > 0 ? (
          results.map((result, index) => (
            <Box key={index}>
              <Typography variant="h6">{result.section}</Typography>
              <Typography variant="body1">{result.content}</Typography>
            </Box>
          ))
        ) : (
          <Typography>No results found.</Typography>
        )}
      </Box>
    </Box>
  );
};

export default Search;
