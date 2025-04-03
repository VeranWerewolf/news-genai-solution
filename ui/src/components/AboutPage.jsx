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
            const modelResponse = await fetch(`${API_BASE_URL}/model-status`, { timeout: 5000 });
            if (modelResponse.ok) {
              const modelData = await modelResponse.json();
              setServiceStatus(prev => ({
                ...prev,
                model: { 
                  status: 'online', 
                  message: `Model ${modelData.name || 'llama3'} is loaded and ready` 
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
}

export default AboutPage;