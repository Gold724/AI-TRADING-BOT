import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RemoteControlPanelProps {
  className?: string;
  apiBaseUrl?: string;
}

interface Strategy {
  strategy: string;
  parameters: Record<string, any>;
  updated_at?: string;
}

interface LogData {
  log_type: string;
  lines: string[];
  filename: string;
  timestamp: string;
}

const RemoteControlPanel: React.FC<RemoteControlPanelProps> = ({ 
  className = '',
  apiBaseUrl = 'http://localhost:5000'
}) => {
  const [health, setHealth] = useState<any>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [logs, setLogs] = useState<LogData | null>(null);
  const [logType, setLogType] = useState<string>('main');
  const [logLines, setLogLines] = useState<number>(50);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [tradeSignal, setTradeSignal] = useState({
    symbol: 'EURUSD',
    side: 'buy',
    quantity: 1
  });

  // Available strategies
  const availableStrategies = [
    { id: 'default', name: 'Default Strategy' },
    { id: 'fibonacci', name: 'Fibonacci Retracement' },
    { id: 'macd', name: 'MACD Crossover' },
    { id: 'rsi', name: 'RSI Oversold/Overbought' }
  ];

  // Available symbols
  const availableSymbols = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'ES'
  ];

  // Fetch health status
  const fetchHealth = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/health`);
      setHealth(response.data);
    } catch (err: any) {
      console.error('Error fetching health:', err);
      setError(`Health check failed: ${err.message}`);
    }
  };

  // Fetch current strategy
  const fetchStrategy = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/api/strategy`);
      setStrategy(response.data);
    } catch (err: any) {
      console.error('Error fetching strategy:', err);
      setError(`Strategy fetch failed: ${err.message}`);
    }
  };

  // Update strategy
  const updateStrategy = async (strategyId: string) => {
    try {
      setLoading(true);
      const response = await axios.post(`${apiBaseUrl}/api/strategy`, {
        strategy: strategyId,
        parameters: {}
      });
      setStrategy(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error updating strategy:', err);
      setError(`Strategy update failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch logs
  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiBaseUrl}/api/logs`, {
        params: {
          type: logType,
          lines: logLines
        }
      });
      setLogs(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching logs:', err);
      setError(`Logs fetch failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Execute trade
  const executeTrade = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${apiBaseUrl}/api/trade`, {
        signal: tradeSignal
      });
      console.log('Trade executed:', response.data);
      setError(null);
      // Refresh logs after trade
      fetchLogs();
    } catch (err: any) {
      console.error('Error executing trade:', err);
      setError(`Trade execution failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchHealth();
    fetchStrategy();
    fetchLogs();

    // Set up polling for health status
    const healthInterval = setInterval(fetchHealth, 30000); // every 30 seconds
    
    return () => {
      clearInterval(healthInterval);
    };
  }, []);

  // Refresh logs when log type or lines change
  useEffect(() => {
    fetchLogs();
  }, [logType, logLines]);

  return (
    <div className={`bg-white p-4 rounded shadow ${className}`}>
      <h2 className="text-xl font-semibold mb-4">Remote Control Panel</h2>
      
      {/* Health Status */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Bot Status</h3>
        {health ? (
          <div className="p-3 bg-gray-100 rounded">
            <p>
              <span className="font-medium">Status:</span>{' '}
              <span className={`${health.status === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
                {health.status === 'ok' ? 'Online' : 'Offline'}
              </span>
            </p>
            <p><span className="font-medium">Environment:</span> {health.environment}</p>
            <p><span className="font-medium">Active Sessions:</span> {health.active_sessions}</p>
            <p><span className="font-medium">Last Updated:</span> {new Date(health.timestamp).toLocaleString()}</p>
          </div>
        ) : (
          <p className="text-gray-500">Loading health status...</p>
        )}
      </div>

      {/* Strategy Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Strategy Selection</h3>
        <div className="grid grid-cols-2 gap-2 mb-3">
          {availableStrategies.map(strat => (
            <button
              key={strat.id}
              className={`p-2 rounded ${strategy?.strategy === strat.id ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              onClick={() => updateStrategy(strat.id)}
              disabled={loading}
            >
              {strat.name}
            </button>
          ))}
        </div>
        {strategy && (
          <div className="p-3 bg-gray-100 rounded">
            <p><span className="font-medium">Current Strategy:</span> {strategy.strategy}</p>
            {strategy.updated_at && (
              <p><span className="font-medium">Last Updated:</span> {new Date(strategy.updated_at).toLocaleString()}</p>
            )}
          </div>
        )}
      </div>

      {/* Trade Execution */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Execute Trade</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Symbol</label>
            <select
              className="w-full p-2 border rounded"
              value={tradeSignal.symbol}
              onChange={(e) => setTradeSignal({...tradeSignal, symbol: e.target.value})}
            >
              {availableSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Side</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                className={`p-2 rounded ${tradeSignal.side === 'buy' ? 'bg-green-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setTradeSignal({...tradeSignal, side: 'buy'})}
              >
                BUY
              </button>
              <button
                className={`p-2 rounded ${tradeSignal.side === 'sell' ? 'bg-red-500 text-white' : 'bg-gray-200'}`}
                onClick={() => setTradeSignal({...tradeSignal, side: 'sell'})}
              >
                SELL
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Quantity</label>
            <input
              type="number"
              className="w-full p-2 border rounded"
              value={tradeSignal.quantity}
              onChange={(e) => setTradeSignal({...tradeSignal, quantity: parseInt(e.target.value) || 1})}
              min="1"
            />
          </div>
          
          <button
            className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
            onClick={executeTrade}
            disabled={loading}
          >
            {loading ? 'Executing...' : 'Execute Trade'}
          </button>
        </div>
      </div>

      {/* Logs Viewer */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Logs</h3>
        <div className="flex space-x-2 mb-2">
          <select
            className="p-2 border rounded"
            value={logType}
            onChange={(e) => setLogType(e.target.value)}
          >
            <option value="main">Main Logs</option>
            <option value="executor">Executor Logs</option>
          </select>
          <select
            className="p-2 border rounded"
            value={logLines}
            onChange={(e) => setLogLines(parseInt(e.target.value))}
          >
            <option value="10">10 lines</option>
            <option value="50">50 lines</option>
            <option value="100">100 lines</option>
          </select>
          <button
            className="p-2 bg-gray-200 rounded hover:bg-gray-300"
            onClick={fetchLogs}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
        
        {logs ? (
          <div className="bg-gray-900 text-green-400 p-3 rounded h-64 overflow-y-auto font-mono text-sm">
            {logs.lines.map((line, index) => (
              <div key={index} className="whitespace-pre-wrap">{line}</div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No logs available</p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-100 text-red-800 rounded mb-4">
          {error}
        </div>
      )}
    </div>
  );
};

export default RemoteControlPanel;