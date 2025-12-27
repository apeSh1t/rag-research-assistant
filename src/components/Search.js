import React, { useState } from 'react';
import { 
  TextField, 
  Button, 
  Box, 
  Typography, 
  Divider, 
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
    <div className="card">
      <div className="card-header">
        <SearchIcon sx={{ color: 'var(--accent)' }} />
        <h3 className="card-title">Semantic Search</h3>
      </div>
      
      <div className="card-body">
        {/* Search bar */}
        <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
          <TextField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            fullWidth
            variant="outlined"
            placeholder="Ask a question or enter keywords..."
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
            onClick={handleSearch} 
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <SearchIcon />}
            disabled={loading}
            className="btn-primary"
          >
            Search
          </Button>
        </Stack>

        {/* Results */}
        <Box>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
              <CircularProgress sx={{ color: 'var(--accent)' }} />
            </Box>
          ) : results.length > 0 ? (
            <Stack spacing={2}>
              <Typography sx={{ color: 'var(--text-muted)', fontSize: 13 }}>
                {results.length} results found
              </Typography>
              {results.map((result, index) => (
                <Box key={index} className="result-item">
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DescriptionIcon sx={{ fontSize: 18, color: 'var(--accent)' }} />
                      <Typography sx={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                        {result.section}
                      </Typography>
                    </Box>
                    <Box className="relevance-badge">
                      {(result.score ?? 0).toFixed(2)}
                    </Box>
                  </Box>
                  <Divider sx={{ my: 1, borderColor: 'var(--border-color)' }} />
                  <Typography sx={{ 
                    whiteSpace: 'pre-wrap', 
                    color: 'var(--text-secondary)', 
                    lineHeight: 1.6,
                    fontSize: 13,
                    pl: 3.5
                  }}>
                    {result.content}
                  </Typography>
                </Box>
              ))}
            </Stack>
          ) : searched ? (
            <div className="empty-state">
              <SearchIcon sx={{ fontSize: 48, color: 'var(--text-muted)', mb: 2 }} />
              <Typography sx={{ color: 'var(--text-muted)' }}>
                No results found. Try different keywords.
              </Typography>
            </div>
          ) : (
            <div className="empty-state">
              <SearchIcon sx={{ fontSize: 48, color: 'var(--text-muted)', mb: 2 }} />
              <Typography sx={{ color: 'var(--text-muted)' }}>
                Enter keywords above to start semantic search
              </Typography>
            </div>
          )}
        </Box>
      </div>
    </div>
  );
};

export default Search;
