import React, { useState } from 'react';

const SearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [enhanceSearch, setEnhanceSearch] = useState(true);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [searchStage, setSearchStage] = useState('');

  // API base URL from environment or default
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Function to search for articles
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setMessage('Please enter a search query.');
      return;
    }

    setIsLoading(true);
    setMessage('Initiating search...');
    setSearchStage('query');

    try {
      // Step 1: Processing query
      setSearchStage('processing');
      setMessage('Processing your query...');
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate processing time
      
      // Step 2: Searching for matches
      setSearchStage('searching');
      setMessage('Searching for relevant articles...');
      
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
      
      // Step 3: Results ready
      setSearchStage('complete');
      
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
      setSearchStage('error');
    } finally {
      setIsLoading(false);
    }
  };

  // Search progress indicator
  const renderSearchProgress = () => {
    if (!searchStage) return null;
    
    const stages = [
      { id: 'query', label: 'Query Received' },
      { id: 'processing', label: 'Processing Query' },
      { id: 'searching', label: 'Searching Articles' },
      { id: 'complete', label: 'Search Complete' }
    ];
    
    const currentIndex = stages.findIndex(stage => stage.id === searchStage);
    
    return (
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {stages.map((stage, index) => (
            <React.Fragment key={stage.id}>
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 flex items-center justify-center rounded-full ${
                  index <= currentIndex ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                } ${searchStage === 'error' && index === currentIndex ? 'bg-red-500' : ''}`}>
                  {index + 1}
                </div>
                <span className={`text-xs mt-1 ${
                  index <= currentIndex ? 'text-blue-600 font-medium' : 'text-gray-500'
                } ${searchStage === 'error' && index === currentIndex ? 'text-red-500' : ''}`}>
                  {stage.label}
                </span>
              </div>
              {index < stages.length - 1 && (
                <div className={`flex-1 h-1 mx-2 ${
                  index < currentIndex ? 'bg-blue-600' : 'bg-gray-200'
                }`}></div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="py-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">Search News Articles</h1>
        
        {/* Search Form */}
        <div className="mb-8 p-6 border rounded-lg bg-white shadow">
          <div className="flex mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-grow p-3 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter search query..."
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="bg-blue-600 text-white px-6 py-3 rounded-r hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
          <div className="flex items-center mb-2">
            <input
              type="checkbox"
              id="enhance-search"
              checked={enhanceSearch}
              onChange={() => setEnhanceSearch(!enhanceSearch)}
              className="w-4 h-4 mr-2 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="enhance-search" className="text-sm text-gray-700">
              Enhance search with AI (uses GenAI to improve search query)
            </label>
          </div>
          <p className="text-xs text-gray-500 italic">
            AI enhancement uses GenAI to expand your query with related terms and improve semantic understanding.
          </p>
        </div>

        {/* Search Progress Indicator */}
        {isLoading && renderSearchProgress()}
        
        {/* Status Message */}
        {message && (
          <div className={`mb-6 p-4 border rounded ${
            message.includes('Error') ? 'bg-red-50 border-red-200 text-red-600' : 'bg-blue-50 border-blue-200 text-blue-600'
          }`}>
            <p className="text-center">{message}</p>
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="p-6 border rounded-lg bg-white shadow">
            <h2 className="text-xl font-semibold mb-4">Search Results</h2>
            <div className="space-y-4">
              {searchResults.map((article, index) => (
                <div key={index} className="p-4 border rounded hover:bg-gray-50 transition-colors">
                  <h3 className="text-lg font-medium mb-2">
                    <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {article.title}
                    </a>
                  </h3>
                  {article.summary && (
                    <p className="mb-2 text-gray-700">{article.summary}</p>
                  )}
                  <div className="flex justify-between items-center mt-2">
                    <div className="text-xs text-gray-500">
                      {article.source && (
                        <span>Source: {article.source}</span>
                      )}
                    </div>
                    {article.topics && article.topics.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {article.topics.map((topic, i) => (
                          <span key={i} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            {topic}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;