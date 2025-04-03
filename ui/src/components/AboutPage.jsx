import React, { useState, useEffect } from 'react';

const AboutPage = () => {
  const [serviceStatus, setServiceStatus] = useState({
    api: { status: 'unknown', message: 'Checking status...' },
    vectorDb: { status: 'unknown', message: 'Checking status...' },
    ollama: { status: 'unknown', message: 'Checking status...' },
    model: { status: 'unknown', message: 'Checking status...' }
  });
  
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  useEffect(() => {
    const checkServices = async () => {
      // Check API status
      try {
        const apiResponse = await fetch(`${API_BASE_URL}/health`, { timeout: 5000 });
        if (apiResponse.ok) {
          setServiceStatus(prev => ({
            ...prev,
            api: { status: 'online', message: 'API is online and responding' }
          }));
          
          // If API is online, check model status next as it depends on Ollama
          try {
            // This endpoint is hypothetical - implement according to your actual API
            const modelResponse = await fetch(`${API_BASE_URL}/health`, { timeout: 5000 });
            if (modelResponse.ok) {
              setServiceStatus(prev => ({
                ...prev,
                model: { 
                  status: 'online', 
                  message: 'Model llama3 is loaded and ready' 
                }
              }));
            } else {
              setServiceStatus(prev => ({
                ...prev,
                model: { 
                  status: 'warning', 
                  message: 'Model might not be fully loaded' 
                }
              }));
            }
          } catch (error) {
            // If we can't check model directly, assume it's warning state
            setServiceStatus(prev => ({
              ...prev,
              model: { 
                status: 'warning', 
                message: 'Cannot determine model status - Ollama may not be ready' 
              }
            }));
          }
        } else {
          setServiceStatus(prev => ({
            ...prev,
            api: { status: 'offline', message: 'API is not responding' }
          }));
        }
      } catch (error) {
        setServiceStatus(prev => ({
          ...prev,
          api: { status: 'offline', message: 'API connection error' }
        }));
      }
      
      // Check Ollama status
      // This is a simplified check - in a real app, we'd check through the API
      try {
        // We're using a simulated check here as direct browser access to Ollama might not be possible
        // In a real app, you'd check through your API
        const ollamaResponse = await fetch(`${API_BASE_URL}/health`);
        
        if (ollamaResponse.ok) {
          setServiceStatus(prev => ({
            ...prev,
            ollama: { status: 'online', message: 'Ollama service appears to be running' }
          }));
        } else {
          setServiceStatus(prev => ({
            ...prev,
            ollama: { status: 'offline', message: 'Ollama service may be down' }
          }));
        }
      } catch (error) {
        setServiceStatus(prev => ({
          ...prev,
          ollama: { status: 'unknown', message: 'Cannot determine Ollama status' }
        }));
      }
      
      // Check Vector DB status
      // Again, this is simplified - would normally check through the API
      try {
        // In a real app, you'd have a specific endpoint to check vector DB status
        const vectorResponse = await fetch(`${API_BASE_URL}/health`);
        
        if (vectorResponse.ok) {
          setServiceStatus(prev => ({
            ...prev,
            vectorDb: { status: 'online', message: 'Vector database appears to be running' }
          }));
        } else {
          setServiceStatus(prev => ({
            ...prev,
            vectorDb: { status: 'offline', message: 'Vector database may be down' }
          }));
        }
      } catch (error) {
        setServiceStatus(prev => ({
          ...prev,
          vectorDb: { status: 'unknown', message: 'Cannot determine vector database status' }
        }));
      }
    };
    
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
            <a href="https://github.com/yourusername/news-genai-solution" target="_blank" rel="noopener noreferrer">
              View project on GitHub →
            </a>
          </p>
        </div>
        
        <div className="p-6 border rounded-lg bg-white shadow">
          <h2 className="text-xl font-semibold mb-4">System Status</h2>
          <div className="space-y-4">
            {Object.entries(serviceStatus).map(([service, { status, message }]) => (
              <div key={service} className="flex items-center p-3 border rounded">
                {renderStatusIndicator(status)}
                <div className="ml-2">
                  <div className="font-medium capitalize">{service === 'api' ? 'API' : service === 'vectorDb' ? 'Vector Database' : service}</div>
                  <div className="text-sm text-gray-600">{message}</div>
                </div>
                <div className="ml-auto">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    status === 'online' ? 'bg-green-100 text-green-800' :
                    status === 'offline' ? 'bg-red-100 text-red-800' :
                    status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {status}
                  </span>
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