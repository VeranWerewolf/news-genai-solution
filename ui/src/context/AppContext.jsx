import React, { createContext, useState, useContext } from 'react';

// Create context
const AppContext = createContext();

// Create provider component
export const AppProvider = ({ children }) => {
  // State for search page
  const [searchQuery, setSearchQuery] = useState('');
  const [enhanceSearch, setEnhanceSearch] = useState(true);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');
  const [searchStage, setSearchStage] = useState('');

  // State for upload page
  const [urls, setUrls] = useState('');
  const [processedUrls, setProcessedUrls] = useState([]);
  const [isUploadLoading, setIsUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadStatus, setUploadStatus] = useState({});
  const [currentStage, setCurrentStage] = useState('');
  const [urlsToProcess, setUrlsToProcess] = useState([]);
  const [processedCount, setProcessedCount] = useState(0);
  const [failedUrls, setFailedUrls] = useState([]);

  // Shared API base URL
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Provide the context value
  const contextValue = {
    // Search state
    searchQuery,
    setSearchQuery,
    enhanceSearch,
    setEnhanceSearch,
    searchResults,
    setSearchResults,
    isSearchLoading,
    setIsSearchLoading,
    searchMessage,
    setSearchMessage,
    searchStage,
    setSearchStage,
    
    // Upload state
    urls,
    setUrls,
    processedUrls,
    setProcessedUrls,
    isUploadLoading,
    setIsUploadLoading,
    uploadMessage,
    setUploadMessage,
    uploadStatus,
    setUploadStatus,
    currentStage,
    setCurrentStage,
    urlsToProcess,
    setUrlsToProcess,
    processedCount,
    setProcessedCount,
    failedUrls,
    setFailedUrls,
    
    // Shared
    API_BASE_URL
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};