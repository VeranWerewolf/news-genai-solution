import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import SearchPage from './SearchPage';
import UploadPage from './UploadPage';
import AboutPage from './AboutPage';

const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="bg-blue-600 shadow-lg">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between">
          <div className="flex space-x-7">
            <div>
              <Link to="/" className="flex items-center py-4 px-2">
                <span className="font-semibold text-white text-lg">News GenAI</span>
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Link to="/" className={`py-4 px-2 ${location.pathname === '/' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}>
              Search
            </Link>
            <Link to="/upload" className={`py-4 px-2 ${location.pathname === '/upload' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}>
              Upload
            </Link>
            <Link to="/about" className={`py-4 px-2 ${location.pathname === '/about' ? 'text-white font-semibold border-b-2 border-white' : 'text-blue-200 hover:text-white'}`}>
              About
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

const AppLayout = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-6xl mx-auto p-4">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
};

export default AppLayout;