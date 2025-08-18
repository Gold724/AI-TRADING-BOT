import React from 'react';
import { createRoot } from 'react-dom/client';
import './src/index.css';

// Import the main App component from src
import MainApp from './src/App';

/**
 * Root App component that serves as the entry point for the React frontend
 * This file redirects to the main App component in the src directory
 */
function App() {
  return <MainApp />;
}

// Render the App component to the DOM
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

export default App;