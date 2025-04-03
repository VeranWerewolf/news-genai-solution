import React, { useState, useEffect } from 'react';

const AboutPage = () => {
  const [serviceStatus, setServiceStatus] = useState({
    api: { status: 'unknown', message: 'Checking status...' },
    vectorDb: { status: 'unknown', message: 'Checking status...' },
    ollama: { status: 'unknown', message: 'Checking status...' },
    model: { status: 'unknown', message: 'Checking status...' }
  });
  
  const [refreshing, setRefreshing] = useState({
    all: false,
    api: false,
    vectorDb: false,
    ollama: false,
    model: false
  });
  
  // Service endpoints from environment variables with fallbacks
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const VECTOR_DB_URL = process.env.REACT_APP_VECTOR_DB_URL || 'http://localhost:6333';
  const OLLAMA_URL = process.env.REACT_APP_OLLAMA_URL || 'http://localhost:11434';
  
  // Use API proxy endpoints for checking services
  // This helps avoid CORS issues with direct requests
  const checkApiStatus = async () => {
    setRefreshing(prev => ({ ...prev, api: true }));
    try {
      // Direct API health check
      const apiResponse = await fetch(`${API_BASE_URL}/health`, { timeout: 5000 });
      if (apiResponse.ok) {
        setServiceStatus(prev => ({
          ...prev,
          api: { status: 'online', message: 'API is online and responding' }
        }));
      } else {
        setServiceStatus(prev => ({
          ...prev,
          api: { status: 'offline', message: 'API is not responding' }
        }));
      }
    } catch (error) {
      setServiceStatus(prev => ({
        ...prev,
        api: { status: 'offline', message: `API connection error: ${error.message}` }
      }));
    } finally {
      setRefreshing(prev => ({ ...prev, api: false }));
    }
  };
  
  const checkModelStatus = async () => {
    setRefreshing(prev => ({ ...prev, model: true }));
    try {
      // Make a test request to Ollama for the model
      const testRequest = {
        model: "llama3",
        prompt: "Hello, are you working?",
        options: {
          temperature: 0.1,
          num_predict: 10
        },
        stream: false
      };
      
      // Direct request to Ollama API
      const modelResponse = await fetch(`${OLLAMA_URL}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testRequest),
        timeout: 10000
      });
      
      if (modelResponse.ok) {
        const result = await modelResponse.json();
        setServiceStatus(prev => ({
          ...prev,
          model: { 
            status: 'online', 
            message: 'Model llama3 is loaded and responding' 
          }
        }));
      } else {
        // Failed to get response
        setServiceStatus(prev => ({
          ...prev,
          model: { 
            status: 'warning', 
            message: 'Model might not be fully loaded or responding' 
          }
        }));
      }
    } catch (error) {
      console.error('Model check error:', error);
      setServiceStatus(prev => ({
        ...prev,
        model: { 
          status: 'warning', 
          message: `Cannot connect to model: ${error.message}` 
        }
      }));
    } finally {
      setRefreshing(prev => ({ ...prev, model: false }));
    }
  };
  
  const checkOllamaStatus = async () => {
    setRefreshing(prev => ({ ...prev, ollama: true }));
    try {
      // Direct request to Ollama API version endpoint
      const response = await fetch(`${OLLAMA_URL}/api/version`);
      
      if (response.ok) {
        try {
          const data = await response.json();
          setServiceStatus(prev => ({
            ...prev,
            ollama: { 
              status: 'online', 
              message: `Ollama is running (version: ${data.version})` 
            }
          }));
        } catch (parseError) {
          // Response may not be JSON
          setServiceStatus(prev => ({
            ...prev,
            ollama: { status: 'online', message: 'Ollama service is responding' }
          }));
        }
      } else {
        setServiceStatus(prev => ({
          ...prev,
          ollama: { status: 'offline', message: `Ollama service error: ${response.status}` }
        }));
      }
    } catch (error) {
      console.error('Ollama check error:', error);
      setServiceStatus(prev => ({
        ...prev,
        ollama: { status: 'unknown', message: `Cannot connect to Ollama: ${error.message}` }
      }));
    } finally {
      setRefreshing(prev => ({ ...prev, ollama: false }));
    }
  };
  
  const checkVectorDbStatus = async () => {
    setRefreshing(prev => ({ ...prev, vectorDb: true }));
    try {
      // Direct request to Vector DB base URL (not /readiness)
      const response = await fetch(`${VECTOR_DB_URL}`);
      
      if (response.ok) {
        try {
          const data = await response.json();
          // Check if response has expected format with version info
          if (data.title && data.version) {
            setServiceStatus(prev => ({
              ...prev,
              vectorDb: { 
                status: 'online', 
                message: `Vector database is online (version: ${data.version})` 
              }
            }));
          } else {
            setServiceStatus(prev => ({
              ...prev,
              vectorDb: { status: 'online', message: 'Vector database is responding' }
            }));
          }
        } catch (parseError) {
          // Response may not be JSON
          setServiceStatus(prev => ({
            ...prev,
            vectorDb: { status: 'online', message: 'Vector database is responding' }
          }));
        }
      } else {
        // Try alternative endpoint if base URL fails
        try {
          const readinessResponse = await fetch(`${VECTOR_DB_URL}/readiness`);
          if (readinessResponse.ok) {
            setServiceStatus(prev => ({
              ...prev,
              vectorDb: { status: 'online', message: 'Vector database is ready' }
            }));
          } else {
            setServiceStatus(prev => ({
              ...prev,
              vectorDb: { status: 'offline', message: 'Vector database is not responding properly' }
            }));
          }
        } catch (readinessError) {
          setServiceStatus(prev => ({
            ...prev,
            vectorDb: { status: 'offline', message: 'Vector database appears to be down' }
          }));
        }
      }
    } catch (error) {
      console.error('Vector DB check error:', error);
      setServiceStatus(prev => ({
        ...prev,
        vectorDb: { status: 'unknown', message: `Cannot connect to vector database: ${error.message}` }
      }));
    } finally {
      setRefreshing(prev => ({ ...prev, vectorDb: false }));
    }
  };
  
  const checkServices = async () => {
    setRefreshing(prev => ({ ...prev, all: true }));
    
    // Check all services in parallel for faster refresh
    await Promise.all([
      checkApiStatus(),
      checkOllamaStatus(),
      checkVectorDbStatus(),
      checkModelStatus()
    ]);
    
    setRefreshing(prev => ({ ...prev, all: false }));
  };
  
  useEffect(() => {
    checkServices();
    
    // Refresh statuses periodically
    const intervalId = setInterval(checkServices, 60000); // Every minute
    
    return () => clearInterval(intervalId);
  }, [API_BASE_URL]);
  
  // Helper to render status indicator
  const renderStatusIndicator = (status) => {
    const statusStyles = {
      online: "bg-green-500",
      offline: "bg-red-500",
      warning: "bg-yellow-500",
      unknown: "bg-gray-400"
    };
    
    return (
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${statusStyles[status] || statusStyles.unknown} mr-2`}></div>
      </div>
    );
  };

  return (
    <div className="py-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">About News GenAI</h1>
        
        <div className="mb-8 p-6 border rounded-lg bg-white shadow">
          <h2 className="text-xl font-semibold mb-4">Application Overview</h2>
          <p className="mb-4">
            News GenAI is a containerized solution for news article scraping, AI-powered analysis, and semantic search.
            The system extracts content from news articles, uses the locally-hosted Llama3 model to generate summaries 
            and identify topics, and stores the processed data in a vector database for efficient semantic search.
          </p>
          
          <h3 className="text-lg font-medium mb-2">Key Features:</h3>
          <ul className="list-disc pl-6 mb-4">
            <li>News extraction from provided URLs</li>
            <li>AI-driven summarization and topic identification</li>
            <li>Semantic search with vector database integration</li>
            <li>Fully containerized deployment with local LLM</li>
          </ul>
          
          <h3 className="text-lg font-medium mb-2">Technical Components:</h3>
          <ul className="list-disc pl-6 mb-4">
            <li><span className="font-medium">News Extraction:</span> Custom Python scraper using BeautifulSoup</li>
            <li><span className="font-medium">GenAI Analysis:</span> Locally-hosted Llama3 model via Ollama</li>
            <li><span className="font-medium">Vector Storage:</span> Qdrant for efficient semantic search</li>
            <li><span className="font-medium">Embeddings:</span> Sentence Transformers</li>
            <li><span className="font-medium">API Layer:</span> FastAPI</li>
            <li><span className="font-medium">UI:</span> React.js with Tailwind CSS</li>
          </ul>
          
          <p className="text-sm text-blue-600 hover:underline">
            <a href="https://github.com/VeranWerewolf/news-genai-solution" target="_blank" rel="noopener noreferrer">
              View project on GitHub →
            </a>
          </p>
        </div>
        
        <div className="p-6 border rounded-lg bg-white shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">System Status</h2>
            <button
              onClick={checkServices}
              disabled={refreshing.all}
              className="text-sm px-3 py-1 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 flex items-center transition-colors disabled:opacity-50"
            >
              {refreshing.all ? (
                <>
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-1"></div>
                  Refreshing...
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh All
                </>
              )}
            </button>
          </div>
          <div className="space-y-4">
            {Object.entries(serviceStatus).map(([service, { status, message }]) => (
              <div key={service} className="flex items-center p-3 border rounded">
                {renderStatusIndicator(status)}
                <div className="ml-2">
                  <div className="font-medium capitalize">{service === 'api' ? 'API' : service === 'vectorDb' ? 'Vector Database' : service}</div>
                  <div className="text-sm text-gray-600">{message}</div>
                </div>
                <div className="ml-auto flex items-center">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    status === 'online' ? 'bg-green-100 text-green-800' :
                    status === 'offline' ? 'bg-red-100 text-red-800' :
                    status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {status}
                  </span>
                  <button
                    onClick={() => {
                      if (service === 'api') checkApiStatus();
                      else if (service === 'vectorDb') checkVectorDbStatus();
                      else if (service === 'ollama') checkOllamaStatus();
                      else if (service === 'model') checkModelStatus();
                    }}
                    disabled={refreshing[service]}
                    className="ml-2 p-1 rounded text-gray-500 hover:bg-gray-100 transition-colors disabled:opacity-50"
                    title={`Refresh ${service} status`}
                  >
                    {refreshing[service] ? (
                      <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;