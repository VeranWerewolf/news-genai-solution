import React, { useState } from 'react';

const NewsGenAI = () => {
  // State for URL input, search query, and results
  const [urls, setUrls] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [enhanceSearch, setEnhanceSearch] = useState(true);
  const [searchResults, setSearchResults] = useState([]);
  const [processedUrls, setProcessedUrls] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  // API base URL from environment or default
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Function to process and store URLs
  const handleProcessUrls = async () => {
    // Split URLs by newline and filter out empty strings
    const urlList = urls.split('\n').filter(url => url.trim() !== '');
    
    if (urlList.length === 0) {
      setMessage('Please enter at least one valid URL.');
      return;
    }

    setIsLoading(true);
    setMessage('Processing URLs...');

    try {
      console.log('Sending request to:', `${API_BASE_URL}/store`);
      console.log('Request payload:', JSON.stringify({ urls: urlList }));
      
      const response = await fetch(`${API_BASE_URL}/store`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ urls: urlList }),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (response.ok) {
        setMessage(`Successfully processed ${data.length} URLs.`);
        setProcessedUrls(data);
        setUrls('');
      } else {
        setMessage(`Error: ${data.detail || 'Failed to process URLs'}`);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      setMessage(`Error: ${error.message || 'Failed to fetch'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to search for articles
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setMessage('Please enter a search query.');
      return;
    }

    setIsLoading(true);
    setMessage('Searching...');

    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          enhance: enhanceSearch,
          limit: 10
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setSearchResults(data);
        setMessage(`Found ${data.length} results.`);
      } else {
        setMessage(`Error: ${data.detail || 'Search failed'}`);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setMessage(`Error: ${error.message}`);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">News GenAI Platform</h1>
      
      {/* Debug Info */}
      <div className="mb-4 p-4 border rounded-lg bg-gray-100 text-sm">
        <p>API URL: {API_BASE_URL}</p>
      </div>
      
      {/* URL Processing Section */}
      <div className="mb-8 p-6 border rounded-lg bg-white shadow">
        <h2 className="text-xl font-semibold mb-4">Process News Articles</h2>
        <div className="mb-4">
          <label className="block mb-2">Enter URLs (one per line):</label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full p-2 border rounded h-32"
            placeholder="https://example.com/article1&#10;https://example.com/article2"
          />
        </div>
        <button
          onClick={handleProcessUrls}
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-blue-300"
        >
          {isLoading ? 'Processing...' : 'Process and Store'}
        </button>
      </div>
      
      {/* Search Section */}
      <div className="mb-8 p-6 border rounded-lg bg-white shadow">
        <h2 className="text-xl font-semibold mb-4">Search Articles</h2>
        <div className="flex mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-grow p-2 border rounded-l"
            placeholder="Enter search query..."
          />
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded-r hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        <div className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={enhanceSearch}
              onChange={() => setEnhanceSearch(!enhanceSearch)}
              className="mr-2"
            />
            Enhance search with AI (uses GenAI to improve search query)
          </label>
        </div>
      </div>
      
      {/* Status Message */}
      {message && (
        <div className="mb-6 p-4 border rounded bg-gray-100">
          <p className="text-center">{message}</p>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="p-6 border rounded-lg bg-white shadow">
          <h2 className="text-xl font-semibold mb-4">Search Results</h2>
          <div className="space-y-4">
            {searchResults.map((article, index) => (
              <div key={index} className="p-4 border rounded">
                <h3 className="text-lg font-medium mb-2">
                  <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {article.title}
                  </a>
                </h3>
                {article.summary && (
                  <p className="mb-2 text-gray-700">{article.summary}</p>
                )}
                {article.topics && article.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {article.topics.map((topic, i) => (
                      <span key={i} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Processed URLs */}
      {processedUrls.length > 0 && (
        <div className="mt-6 p-6 border rounded-lg bg-white shadow">
          <h2 className="text-xl font-semibold mb-4">Processed Articles</h2>
          <p className="mb-2">Successfully processed and stored the following article IDs:</p>
          <div className="bg-gray-100 p-4 rounded overflow-x-auto">
            <code>{processedUrls.join(', ')}</code>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsGenAI;