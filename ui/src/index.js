import React from 'react';
import ReactDOM from 'react-dom/client';
import NewsGenAI from './components/NewsGenAI';
import './index.css';

const App = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <NewsGenAI />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);