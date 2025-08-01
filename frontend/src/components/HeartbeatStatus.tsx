import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface HeartbeatStatusProps {
  className?: string;
  apiBaseUrl?: string;
  pollingInterval?: number; // in milliseconds
}

interface HeartbeatData {
  status: string;
  timestamp: string;
  session_active: boolean;
}

const HeartbeatStatus: React.FC<HeartbeatStatusProps> = ({
  className = '',
  apiBaseUrl = 'http://localhost:5000',
  pollingInterval = 10000 // Default to 10 seconds
}) => {
  const [heartbeatData, setHeartbeatData] = useState<HeartbeatData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch heartbeat status
  const fetchHeartbeatStatus = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/heartbeat/status`);
      setHeartbeatData(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching heartbeat status:', err);
      setError(`Heartbeat status check failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Set up polling for heartbeat status
  useEffect(() => {
    // Initial fetch
    fetchHeartbeatStatus();

    // Set up polling interval
    const interval = setInterval(fetchHeartbeatStatus, pollingInterval);

    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, [apiBaseUrl, pollingInterval]);

  // Helper function to format timestamp
  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      return timestamp; // Return original if parsing fails
    }
  };

  // Helper function to determine status color
  const getStatusColor = (status: string, isActive: boolean): string => {
    if (!isActive) return 'text-gray-500';
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('error') || statusLower.includes('fail')) {
      return 'text-red-600';
    } else if (statusLower.includes('trade executed') || statusLower.includes('profit')) {
      return 'text-green-600';
    } else if (statusLower.includes('login successful')) {
      return 'text-blue-600';
    } else {
      return 'text-yellow-600'; // Default for other active states
    }
  };

  return (
    <div className={`bg-white p-4 rounded shadow ${className}`}>
      <h2 className="text-xl font-semibold mb-3">Sentinel Heartbeat</h2>
      
      {loading && !heartbeatData ? (
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      ) : error ? (
        <div className="p-3 bg-red-100 text-red-800 rounded">
          {error}
        </div>
      ) : heartbeatData ? (
        <div className="space-y-2">
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${heartbeatData.session_active ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className={`font-medium ${getStatusColor(heartbeatData.status, heartbeatData.session_active)}`}>
              {heartbeatData.status}
            </span>
          </div>
          <p className="text-sm text-gray-600">
            Last update: {formatTimestamp(heartbeatData.timestamp)}
          </p>
        </div>
      ) : (
        <p className="text-gray-500">No heartbeat data available</p>
      )}
    </div>
  );
};

export default HeartbeatStatus;