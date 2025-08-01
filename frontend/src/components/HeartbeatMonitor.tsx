import React, { useState, useEffect } from 'react';
import axios from 'axios';
import HeartbeatStatus from './HeartbeatStatus';

interface HeartbeatMonitorProps {
  className?: string;
  apiBaseUrl?: string;
  pollingInterval?: number; // in milliseconds
  showTitle?: boolean;
}

const HeartbeatMonitor: React.FC<HeartbeatMonitorProps> = ({
  className = '',
  apiBaseUrl = 'http://localhost:5000',
  pollingInterval = 10000,
  showTitle = true
}) => {
  return (
    <div className={`${className}`}>
      {showTitle && (
        <h2 className="text-xl font-semibold mb-3">Sentinel Heartbeat Monitor</h2>
      )}
      
      <div className="grid grid-cols-1 gap-4">
        <HeartbeatStatus 
          apiBaseUrl={apiBaseUrl} 
          pollingInterval={pollingInterval} 
          className="h-full"
        />
        
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-lg font-medium mb-2">Heartbeat Controls</h3>
          <div className="space-y-2">
            <button 
              className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              onClick={() => window.open(`${apiBaseUrl}/api/status`, '_blank')}
            >
              View Full Status
            </button>
            
            <button 
              className="w-full p-2 bg-gray-200 rounded hover:bg-gray-300"
              onClick={() => window.open(`${apiBaseUrl}/api/logs?type=main&lines=100`, '_blank')}
            >
              View Logs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeartbeatMonitor;