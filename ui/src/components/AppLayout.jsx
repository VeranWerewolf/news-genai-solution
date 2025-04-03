import React, { useState } from 'react';
import SearchPage from './SearchPage';
import UploadPage from './UploadPage';
import AboutPage from './AboutPage';
import { AppProvider } from '../context/AppContext';

const AppLayout = () => {
  const [activeTab, setActiveTab] = useState('search');

  const renderTab = () => {
    switch (activeTab) {
      case 'search':
        return <SearchPage />;
      case 'upload':
        return <UploadPage />;
      case 'about':
        return <AboutPage />;
      default:
        return <SearchPage />;
    }
  };

  return (
    <AppProvider>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-blue-600 shadow-lg">
          <div className="max-w-6xl mx-auto px-4">
            <div className="flex justify-between">
              <div className="flex space-x-7">
                <div>
                  <button onClick={() => setActiveTab('search')} className="flex items-center py-4 px-2">
                    <span className="font-semibold text-white text-lg">News GenAI</span>
                  </button>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`py-4 px-2 ${activeTab === 'search' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}
                >
                  Search
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`py-4 px-2 ${activeTab === 'upload' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}
                >
                  Upload
                </button>
                <button
                  onClick={() => setActiveTab('about')}
                  className={`py-4 px-2 ${activeTab === 'about' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}
                >
                  About
                </button>
              </div>
            </div>
          </div>
        </nav>
        <div className="max-w-6xl mx-auto p-4">
          {renderTab()}
        </div>
      </div>
    </AppProvider>
  );
};

export default AppLayout;