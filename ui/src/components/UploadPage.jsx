import React, { useEffect } from 'react';
import { useAppContext } from '../context/AppContext';

const UploadPage = () => {
  const {
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
    API_BASE_URL
  } = useAppContext();

  // Process URLs one by one to provide better feedback
  useEffect(() => {
    const processNextUrl = async () => {
      if (urlsToProcess.length === 0 || !isUploadLoading) return;
      
      const url = urlsToProcess[0];
      const remainingUrls = urlsToProcess.slice(1);
      
      try {
        setUploadStatus(prev => ({
          ...prev,
          [url]: { status: 'processing', message: 'Processing article...' }
        }));
        
        // Step 1: Extraction
        setCurrentStage('extracting');
        setUploadStatus(prev => ({
          ...prev,
          [url]: { status: 'extracting', message: 'Extracting content...' }
        }));
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate processing time
        
        // Step 2: Analysis
        setCurrentStage('analyzing');
        setUploadStatus(prev => ({
          ...prev,
          [url]: { status: 'analyzing', message: 'Analyzing with GenAI...' }
        }));
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate processing time
        
        // Step 3: Storage
        setCurrentStage('storing');
        setUploadStatus(prev => ({
          ...prev,
          [url]: { status: 'storing', message: 'Storing in vector database...' }
        }));
        
        // Actual API call
        const response = await fetch(`${API_BASE_URL}/store`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ urls: [url] }),
        });

        const data = await response.json();
        
        if (response.ok) {
          setProcessedUrls(prev => [...prev, ...data]);
          setUploadStatus(prev => ({
            ...prev,
            [url]: { status: 'success', message: 'Successfully processed article' }
          }));
          setProcessedCount(prev => prev + 1);
        } else {
          setUploadStatus(prev => ({
            ...prev,
            [url]: { status: 'error', message: data.detail || 'Failed to process article' }
          }));
          setFailedUrls(prev => [...prev, url]);
        }
      } catch (error) {
        console.error(`Error processing URL ${url}:`, error);
        setUploadStatus(prev => ({
          ...prev,
          [url]: { status: 'error', message: error.message || 'Network error' }
        }));
        setFailedUrls(prev => [...prev, url]);
      }
      
      // Continue with next URL or finish
      if (remainingUrls.length > 0) {
        setUrlsToProcess(remainingUrls);
      } else {
        setIsUploadLoading(false);
        setCurrentStage('complete');
        
        // Set final message
        if (failedUrls.length === 0) {
          setUploadMessage(`Successfully processed all ${processedCount + 1} articles`);
        } else {
          setUploadMessage(`Processed ${processedCount + 1} articles. Failed: ${failedUrls.length}`);
        }
      }
    };

    processNextUrl();
  }, [urlsToProcess, isUploadLoading, API_BASE_URL, failedUrls, processedCount, setCurrentStage, setFailedUrls, setIsUploadLoading, setProcessedCount, setProcessedUrls, setUploadMessage, setUploadStatus, setUrlsToProcess]);

  // Function to process and store URLs
  const handleProcessUrls = async () => {
    // Split URLs by newline and filter out empty strings
    const urlList = urls.split('\n').filter(url => url.trim() !== '');
    
    if (urlList.length === 0) {
      setUploadMessage('Please enter at least one valid URL.');
      return;
    }

    // Reset states
    setIsUploadLoading(true);
    setUploadMessage(`Starting to process ${urlList.length} URLs...`);
    setProcessedUrls([]);
    setFailedUrls([]);
    setProcessedCount(0);
    setCurrentStage('preparing');
    
    // Initialize upload status for each URL
    const initialStatus = {};
    urlList.forEach(url => {
      initialStatus[url] = { status: 'pending', message: 'Waiting to process' };
    });
    setUploadStatus(initialStatus);
    
    // Start processing
    setUrlsToProcess(urlList);
  };

  // Display the processing stages
  const renderProcessStages = () => {
    const stages = [
      { id: 'preparing', label: 'Preparing' },
      { id: 'extracting', label: 'Extracting Content' },
      { id: 'analyzing', label: 'Analyzing with GenAI' },
      { id: 'storing', label: 'Storing in Database' },
      { id: 'complete', label: 'Process Complete' }
    ];
    
    const currentIndex = stages.findIndex(stage => stage.id === currentStage);
    
    if (currentIndex === -1) return null;
    
    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-2">Processing Status</h3>
        <div className="flex items-center justify-between mb-4">
          {stages.map((stage, index) => (
            <React.Fragment key={stage.id}>
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 flex items-center justify-center rounded-full ${
                  index <= currentIndex ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  {index + 1}
                </div>
                <span className={`text-xs mt-1 ${
                  index <= currentIndex ? 'text-blue-600 font-medium' : 'text-gray-500'
                }`}>
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
        <div className="text-sm text-gray-600 text-center">
          {processedCount} of {Object.keys(uploadStatus).length} articles processed
          {failedUrls.length > 0 && ` (${failedUrls.length} failed)`}
        </div>
      </div>
    );
  };

  return (
    <div className="py-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">Upload News Articles</h1>
        
        {/* URL Processing Form */}
        <div className="mb-8 p-6 border rounded-lg bg-white shadow">
          <h2 className="text-xl font-semibold mb-4">Process News Articles</h2>
          <div className="mb-4">
            <label className="block mb-2 font-medium">Enter URLs (one per line):</label>
            <textarea
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              className="w-full p-3 border rounded h-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="https://example.com/article1&#10;https://example.com/article2"
              disabled={isUploadLoading}
            />
          </div>
          <button
            onClick={handleProcessUrls}
            disabled={isUploadLoading}
            className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
          >
            {isUploadLoading ? 'Processing...' : 'Process and Store'}
          </button>
        </div>
        
        {/* Processing Stages Indicator */}
        {isUploadLoading && renderProcessStages()}
        
        {/* Status Message */}
        {uploadMessage && (
          <div className={`mb-6 p-4 border rounded ${
            uploadMessage.includes('Failed') ? 'bg-red-50 border-red-200 text-red-600' : 'bg-blue-50 border-blue-200 text-blue-600'
          }`}>
            <p className="text-center">{uploadMessage}</p>
          </div>
        )}
        
        {/* URL Processing Status */}
        {Object.keys(uploadStatus).length > 0 && (
          <div className="p-6 border rounded-lg bg-white shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">URL Processing Status</h2>
            <div className="space-y-3">
              {Object.entries(uploadStatus).map(([url, status]) => (
                <div key={url} className="p-3 border rounded flex items-center">
                  <div className="flex-shrink-0 mr-3">
                    {status.status === 'success' && (
                      <div className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {status.status === 'error' && (
                      <div className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {['pending', 'processing', 'extracting', 'analyzing', 'storing'].includes(status.status) && (
                      <div className="w-6 h-6 flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      </div>
                    )}
                  </div>
                  <div className="flex-grow">
                    <div className="truncate text-sm font-medium">{url}</div>
                    <div className={`text-xs ${
                      status.status === 'error' ? 'text-red-600' : 
                      status.status === 'success' ? 'text-green-600' : 'text-blue-600'
                    }`}>
                      {status.message}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Processed URLs */}
        {processedUrls.length > 0 && (
          <div className="p-6 border rounded-lg bg-white shadow">
            <h2 className="text-xl font-semibold mb-4">Successfully Processed Articles</h2>
            <p className="mb-2">The following article IDs have been added to the database:</p>
            <div className="bg-gray-100 p-4 rounded overflow-x-auto">
              <code className="text-sm break-all">{processedUrls.join(', ')}</code>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;