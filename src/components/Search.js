import React, { useState } from 'react';
import { 
  TextField, 
  Button, 
  Box, 
  Typography, 
  Paper, 
  Divider, 
  Chip,
  Stack,
  CircularProgress
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DescriptionIcon from '@mui/icons-material/Description';
import { API_ENDPOINTS } from '../config';

const Search = ({ searchState, setSearchState }) => {
  const { query, results, searched } = searchState;
  const [loading, setLoading] = useState(false);

  const setQuery = (newQuery) => {
    setSearchState(prev => ({ ...prev, query: newQuery }));
  };

  const setResults = (newResults) => {
    setSearchState(prev => ({ ...prev, results: newResults }));
  };

  const setSearched = (val) => {
    setSearchState(prev => ({ ...prev, searched: val }));
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const response = await fetch(API_ENDPOINTS.SEARCH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      const searchData = await response.json();

      if (response.ok) {
        setResults(searchData.data || []);
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Stack direction="row" spacing={2} sx={{ mb: 4 }}>
        <TextField
          label="搜索文档内容 (语义搜索)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          fullWidth
          variant="outlined"
          placeholder="输入问题或关键词，例如：如何计算稀释比例？"
        />
        <Button 
          variant="contained" 
          onClick={handleSearch} 
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
          disabled={loading}
          sx={{ minWidth: 120 }}
        >
          搜索
        </Button>
      </Stack>

      <Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : results.length > 0 ? (
          <Stack spacing={3}>
            <Typography variant="subtitle2" color="textSecondary">
              找到 {results.length} 条相关结果：
            </Typography>
            {results.map((result, index) => (
              <Paper key={index} variant="outlined" sx={{ p: 2, bgcolor: '#fcfcfc' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <DescriptionIcon sx={{ fontSize: 20, mr: 1, color: 'primary.main' }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', flexGrow: 1 }}>
                    {result.section}
                  </Typography>
                  <Chip 
                    label={`相关度: ${(1 - result.score / 2).toFixed(2)}`} 
                    size="small" 
                    color="primary" 
                    variant="outlined" 
                  />
                </Box>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', color: 'text.primary', lineHeight: 1.6 }}>
                  {result.content}
                </Typography>
              </Paper>
            ))}
          </Stack>
        ) : searched ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography color="textSecondary">未找到相关内容，请尝试更换关键词。</Typography>
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 8, border: '1px dashed #ccc', borderRadius: 2 }}>
            <Typography color="textSecondary">在上方输入内容开始语义搜索</Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default Search;
